"""Karaoke for a movie's song: from the user's lyrics file and the Whisper alignment to karaoke segments.

    .venv-whisper/Scripts/python.exe tools/whisper_tool.py align <wav> <lyrics.txt> <timing.json>   # timings only
    python tools/karaoke_spec.py MOVIE003 [--from SECONDS] [--to SECONDS] [--layout bottom|strip|overlay]

Lyrics: work/translation/en/movies/lyrics/<movie>.txt, written by the user ("romaji || English" per sung row; see
the file header). The segments written into work/translation/en/movies/<movie>.json hold only timings and the
row index: the lyric text is read from the user's file when the movie is built, so no lyrics are stored in the
specs or committed. Rows the alignment could not find are left out.

Layout: the romaji row sits above the translation row at the bottom of the frame; the romaji fills from left to
right word by word as it is sung; a translation that covers several rows stays on screen across them.
"""
import hashlib
import json
import sys
import movie_text as mt

FPS = 30000 / 1001
LAYOUTS = {
    # full width at the bottom of the frame
    'bottom': ({'align': 'center', 'x': 256, 'size': 17, 'weight': 650},
               {'align': 'center', 'x': 256, 'size': 14, 'weight': 600}, 470, 441),
    # bottom of the ending's left video strip (x 35-210), clear of the scrolling credits
    'strip': ({'align': 'center', 'x': 122, 'size': 13, 'weight': 650},
              {'align': 'center', 'x': 122, 'size': 11, 'weight': 600}, 168, 428),
    # Larger lyrics over the ending credits, with a dark translucent backing.
    'overlay': ({'align': 'center', 'x': 256, 'size': 18, 'weight': 650},
                {'align': 'center', 'x': 256, 'size': 15, 'weight': 600}, 470, 432),
}


def build(movie, t_from=0.0, t_to=1e9, layout='bottom'):
    ROMAJI, ENGLISH, width, bottom = LAYOUTS[layout]
    lyrics_rel = 'work/translation/en/movies/lyrics/%s.txt' % movie
    rows = mt.read_lyrics(mt.ROOT / lyrics_rel)
    timing_data = json.loads((mt.CACHE / ('%s.lyrics_timing.json' % movie)).read_text(encoding='utf-8'))
    mt.require(timing_data.get('lyrics_sha256') == hashlib.sha256((mt.ROOT/lyrics_rel).read_bytes()).hexdigest(),
               'Lyrics changed since alignment; align them again')
    timing = timing_data['rows']
    timed = [t for t in timing if 'start' in t and t_from <= t['start'] <= t_to]
    mt.require(all(a['start'] < b['start'] for a,b in zip(timed,timed[1:])), 'Lyric onsets are out of order')
    face = mt.lyric_face(ROMAJI)
    segments = []
    for k, t in enumerate(timed):
        roma, english = rows[t['row']]
        start, end = t['start'], t['end']
        nxt = timed[k + 1]['start'] if k + 1 < len(timed) else None
        a = max(0, round((start - 0.45) * FPS), segments[-1]['frames'][1] if segments else 0)
        b = round((min(end + 0.35, nxt - 0.12) if nxt else end + 0.8) * FPS)
        mt.require(a < b and 0 < end-start < 20, 'Implausible lyric timing at row %d' % t['row'])
        full = face.getlength(roma) or 1.0
        knots = [[a, 0.0]]
        finish = min(round(end * FPS), b - 4)
        for col, when in t['words']:
            knots.append([max(a, min(round(when * FPS), finish)), face.getlength(roma[:col]) / full])
        knots.append([finish, 1.0])
        knots = sorted({kn[0]: kn for kn in knots}.values())
        # keep the fraction monotonic
        for i in range(1, len(knots)):
            knots[i][1] = max(knots[i][1], knots[i - 1][1])
        eng_lines = len(mt.lyric_wrap(english or '', ENGLISH, width))
        roma_bottom = bottom - eng_lines * (ENGLISH['size']+5) - 6
        segments.append({'type': 'karaoke', 'frames': [a, b], 'lyrics': lyrics_rel, 'index': t['row'],
                         'romaji_line': ROMAJI, 'english_line': ENGLISH, 'romaji_bottom': roma_bottom,
                         'show_english': False, 'width': width, 'knots': knots, 'fade': 4, 'fill': [215,60,145]})
        if layout == 'overlay':
            roma_lines = len(mt.lyric_wrap(roma, ROMAJI, width))
            top = roma_bottom - roma_lines * (ROMAJI['size']+5) - 8
            segments[-1]['backdrop'] = {'top': top, 'bottom': mt.H, 'opacity': .86, 'feather': 8}
    captions = []
    for s in segments:
        english = rows[s['index']][1]
        if not english:
            continue
        if (captions and rows[captions[-1]['index']][1] == english and
                s['frames'][0]-captions[-1]['frames'][1] < 20):
            captions[-1]['frames'][1] = s['frames'][1]
        else:
            captions.append({'type': 'lyrics_caption', 'frames': list(s['frames']), 'lyrics': lyrics_rel,
                             'index': s['index'], 'line': ENGLISH, 'width': width, 'bottom': bottom,
                             'colour': [235,128,128], 'fade': 4})
    path = mt.SPEC / ('%s.json' % movie)
    spec = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'movie': movie, 'segments': []}
    spec['segments'] = [s for s in spec['segments'] if s.get('type') not in ('karaoke','lyrics_caption')] + segments + captions
    spec['karaoke_review'] = {'layout': layout, 'timed_rows': len(segments),
                              'omitted_rows': [t['row'] for t in timing if 'start' not in t],
                              'lyrics_sha256': timing_data['lyrics_sha256']}
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding='utf-8')
    print(movie, len(segments), 'karaoke rows of', len(rows), '(%d omitted)' % (len(timing) - len(timed)))


if __name__ == '__main__':
    args = sys.argv[1:]
    t_from = float(args[args.index('--from') + 1]) if '--from' in args else 0.0
    t_to = float(args[args.index('--to') + 1]) if '--to' in args else 1e9
    layout = args[args.index('--layout') + 1] if '--layout' in args else 'bottom'
    build(args[0], t_from, t_to, layout)
