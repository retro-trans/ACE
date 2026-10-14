"""Whisper (faster-whisper, run with the 64-bit venv: .venv-whisper/Scripts/python.exe tools/whisper_tool.py ...).

    speech <wav> <out.json>   Japanese speech transcript with timings (dialogue / narration to subtitle)
    timing <wav> <out.json>   timings only, for songs: sung phrases and their word onsets. The recognised text is
                              discarded and never stored (song lyrics are supplied by the user, not taken from here).
"""
import json
import os
import sys
import sysconfig
from pathlib import Path

# CUDA runtime DLLs come from the nvidia-* wheels in the venv; register their folders before ctranslate2 loads.
for _bin in (Path(sysconfig.get_paths()['purelib']) / 'nvidia').glob('*/bin'):
    os.add_dll_directory(str(_bin))
    os.environ['PATH'] = str(_bin) + os.pathsep + os.environ.get('PATH', '')
from faster_whisper import WhisperModel  # noqa: E402


def model():
    return WhisperModel('large-v3', device='cuda', compute_type='float16')


def speech(wav, out):
    segs, info = model().transcribe(wav, language='ja', vad_filter=True, word_timestamps=False, beam_size=5)
    rows = [{'start': round(s.start, 2), 'end': round(s.end, 2), 'ja': s.text.strip()} for s in segs]
    json.dump({'source': wav, 'segments': rows}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(rows), 'segments ->', out)


def timing(wav, out):
    segs, info = model().transcribe(wav, language='ja', vad_filter=False, word_timestamps=True, beam_size=5,
                                    condition_on_previous_text=False)
    rows = []
    for s in segs:
        words = [[round(w.start, 2), round(w.end, 2)] for w in (s.words or [])]
        rows.append({'start': round(s.start, 2), 'end': round(s.end, 2), 'words': words})
    json.dump({'source': wav, 'phrases': rows}, open(out, 'w', encoding='utf-8'), indent=1)
    print(len(rows), 'phrases ->', out)


def _letters(text):
    """Normalised romaji letters for matching: lower case, long vowels and particle spellings folded."""
    import re
    import unicodedata
    t = re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', text.lower()))
    for a, b in (('wo', 'o'), ('ou', 'o'), ('oo', 'o'), ('uu', 'u'), ('aa', 'a'), ('ii', 'i'), ('ee', 'e')):
        t = t.replace(a, b)
    return t


def align(wav, lyrics, out, t_from=0.0, t_to=None, selected=None):
    """Time the user's romaji lyric rows against the song: the recognised words are converted to romaji in memory
    and matched letter by letter to the lyrics; only the timings are written (row index, start, end, and the
    onset of every word of the row as [character index, time])."""
    import difflib
    import re
    import pykakasi
    from lyrics import read_lyrics
    from faster_whisper.audio import decode_audio
    import hashlib
    kks = pykakasi.kakasi()
    rows = [r for r, _ in read_lyrics(lyrics)]
    row_ids = list(range(len(rows)))
    if selected:
        row_ids = []
        for part in selected.split(','):
            lo, _, hi = part.partition('-')
            row_ids.extend(range(int(lo), int(hi or lo)+1))
        rows = [rows[i] for i in row_ids]
    samples = decode_audio(wav, sampling_rate=16000)
    t_to = min(t_to if t_to is not None else len(samples)/16000, len(samples)/16000)
    samples = samples[round(t_from*16000):round(t_to*16000)]
    segs, _ = model().transcribe(samples, language='ja', vad_filter=False, word_timestamps=True, beam_size=5,
                                 condition_on_previous_text=False)
    heard, times = [], []
    for s in segs:
        for w in s.words or []:
            roma = _letters(''.join(x['hepburn'] for x in kks.convert(w.word)))
            for k, ch in enumerate(roma):
                heard.append(ch)
                times.append(t_from + w.start + (w.end - w.start) * k / max(1, len(roma)))
    # lyric letters with (row, character index in the row) for each
    lyr, where = [], []
    for r, text in enumerate(rows):
        for m in re.finditer(r'[^\W\d_]+', text, re.UNICODE):
            norm = _letters(m.group())
            for k, ch in enumerate(norm):
                lyr.append(ch)
                where.append((r, m.start() + round(k * len(m.group()) / max(1, len(norm)))))
    sm = difflib.SequenceMatcher(None, ''.join(lyr), ''.join(heard), autojunk=False)
    at = [None] * len(lyr)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            at[a + k] = times[b + k]
    known = [i for i, t in enumerate(at) if t is not None]
    result = []
    for r in range(len(rows)):
        idx = [i for i in range(len(lyr)) if where[i][0] == r]
        hits = [i for i in idx if at[i] is not None]
        if len(hits) < max(4, len(idx) * .5):
            result.append({'row': row_ids[r], 'matched': len(hits), 'letters': len(idx)})
            continue
        def t_of(i):
            if at[i] is not None:
                return at[i]
            lo = max((k for k in hits if k < i), default=None)
            hi = min((k for k in hits if k > i), default=None)
            if lo is None or hi is None:
                return at[hits[0]] if lo is None else at[hits[-1]]
            return at[lo] + (at[hi] - at[lo]) * (i - lo) / (hi - lo)
        words, seen = [], set()
        for i in idx:
            col = where[i][1]
            text = rows[r]
            start_of_word = col == 0 or text[col - 1] == ' '
            if start_of_word and col not in seen:
                seen.add(col)
                words.append([col, round(t_of(i), 3)])
        result.append({'row': row_ids[r], 'start': round(t_of(idx[0]), 3), 'end': round(t_of(idx[-1]) + 0.25, 3),
                       'words': words, 'matched': len(hits), 'letters': len(idx)})
    json.dump({'source': wav, 'lyrics_sha256': hashlib.sha256(Path(lyrics).read_bytes()).hexdigest(),
               'window': [t_from, t_to], 'rows': result}, open(out, 'w', encoding='utf-8'), indent=1)
    print(len(rows), 'rows,', sum(1 for x in result if 'start' in x), 'timed ->', out)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'align':
        start = float(sys.argv[sys.argv.index('--from')+1]) if '--from' in sys.argv else 0.0
        end = float(sys.argv[sys.argv.index('--to')+1]) if '--to' in sys.argv else None
        selected = sys.argv[sys.argv.index('--rows')+1] if '--rows' in sys.argv else None
        align(sys.argv[2], sys.argv[3], sys.argv[4], start, end, selected)
    else:
        {'speech': speech, 'timing': timing}[cmd](sys.argv[2], sys.argv[3])
