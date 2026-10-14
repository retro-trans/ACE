"""Subtitles and title cards in the story movies (MOVIE1): from scan results to translation cards to movie specs.

    python tools/subtitle_spec.py cards M1_MOVIE001 [...]   # work/translation/en/movies/subs/<movie>.json (+ crops)
    python tools/subtitle_spec.py spec  M1_MOVIE001 [...]   # work/translation/en/movies/<movie>.json for movie_text

Cards file: {"movie", "cards": [{"id", "frames": [a, b], "kind": "subtitle"|"title", "box": [x0, y0, x1, y1],
"lines": [[y0, y1], ...], "ja": "...", "en": "..."}]}. Translators fill "ja" (transcription, one line per
Japanese line, "\\n" between) and "en". English is centred on the card and broken into as many lines as the
Japanese had (or set "en" with explicit "\\n"). Cards without "en" are left untouched; "skip": true marks a
false detection.

Each card becomes a static segment: the card area is restored from the nearest frames before and after it
without text (falling back to black), and the English follows the original lettering's fade.
"""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import movie_text as mt

SUBS = mt.SPEC / 'subs'
SIZE = {'subtitle': 15, 'title': 16}
WEIGHT = {'subtitle': 600, 'title': 700}


def cards(movie):
    scan = json.loads((mt.VIEW / ('%s_subs.json' % movie)).read_text(encoding='utf-8'))
    rows = np.load(mt.CACHE / ('%s_rows.npy' % movie))
    es, _ = mt.elementary(movie)
    segs = scan['segments']
    peaks = {s['peak'] for s in segs}
    frame = {}
    for n, buf in mt.frames(es, 0, scan['frames']):
        if n in peaks:
            frame[n] = mt.planes(buf)[0]
    # keep lines on a dark background, group lines shown over the same frames into one card
    lines = []
    for s in segs:
        Y = frame[s['peak']]
        lo, hi = s['band']
        sub = Y[lo:hi]
        ink = (sub - mt.box(sub, 3) > 35) & (sub > 110)
        if np.median(sub[~mt.dilate(ink, 2)]) > 40:
            continue                                   # moving picture behind: not a caption
        cols = np.where(ink.any(axis=0))[0]
        if len(cols) < 5:
            continue
        lines.append({'frames': s['frames'], 'band': [lo, hi], 'x': [int(cols.min()), int(cols.max()) + 1],
                      'peak': s['peak']})
    groups = []
    for l in sorted(lines, key=lambda l: (l['frames'][0], l['band'][0])):
        for g in groups:
            a, b = g['frames']
            ov = min(b, l['frames'][1]) - max(a, l['frames'][0])
            if ov > 0.6 * min(b - a, l['frames'][1] - l['frames'][0]) and abs(l['band'][0] - g['lines'][-1][1]) < 12:
                g['lines'].append(l['band'])
                g['frames'] = [min(a, l['frames'][0]), max(b, l['frames'][1])]
                g['x'] = [min(g['x'][0], l['x'][0]), max(g['x'][1], l['x'][1])]
                break
        else:
            groups.append({'frames': list(l['frames']), 'lines': [l['band']], 'x': list(l['x']), 'peak': l['peak']})
    out, old = [], {}
    path = SUBS / ('%s.json' % movie)
    if path.exists():
        old = {tuple(c['frames']): c for c in json.loads(path.read_text(encoding='utf-8'))['cards']}
    for i, g in enumerate(groups):
        y0, y1 = g['lines'][0][0], g['lines'][-1][1]
        kind = 'title' if y1 < 330 else 'subtitle'
        c = {'id': i, 'frames': g['frames'], 'kind': kind, 'box': [g['x'][0], y0, g['x'][1], y1],
             'lines': g['lines'], 'peak': g['peak'], 'ja': '', 'en': ''}
        prev = old.get(tuple(g['frames']))
        if prev and prev.get('manual'):
            c = dict(prev)
        elif prev:
            c.update({k: prev[k] for k in ('ja', 'en', 'skip', 'notes', 'kind', 'box', 'lines') if k in prev})
        out.append(c)
    # Cards added or reshaped by hand (no scan match, or marked "manual") are kept as they are.
    seen = {tuple(c['frames']) for c in out}
    for key, prev in old.items():
        if key not in seen and (prev.get('manual') or prev.get('en')):
            out.append(dict(prev, id=len(out)))
    out.sort(key=lambda c: c['frames'][0])
    SUBS.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'movie': movie, 'cards': out}, ensure_ascii=False, indent=1), encoding='utf-8')
    # crop sheet: one strip per card, numbered by id
    tiles = []
    for c in out:
        x0, y0, x1, y1 = c['box']
        t = Image.fromarray(np.clip(frame[c['peak']][max(0, y0 - 4):y1 + 4], 0, 255).astype(np.uint8))
        t = t.resize((mt.W * 2, t.height * 2), Image.LANCZOS).convert('RGB')
        ImageDraw.Draw(t).text((2, 0), '#%d f%d-%d %s' % (c['id'], c['frames'][0], c['frames'][1], c['kind']),
                               fill=(255, 255, 0))
        tiles.append(t)
    if tiles:
        sheet = Image.new('RGB', (mt.W * 2, sum(t.height + 4 for t in tiles)), (60, 0, 0))
        y = 0
        for t in tiles:
            sheet.paste(t, (0, y))
            y += t.height + 4
        sheet.save(mt.VIEW / ('%s_cards.png' % movie))
    print(movie, len(out), 'cards ->', path)


def quiet(rows, lo, hi, n, step, limit, total):
    e = rows[:, lo:hi].sum(axis=1)
    k = n
    for _ in range(limit):
        k += step
        if not 0 <= k < total:
            return None
        if e[k] < 4:
            return k
    return None


def text_rows(Y, box):
    """Row runs of lettering inside ``box`` (x0, y0, x1, y1) of frame ``Y``: [[top, bottom), ...]."""
    x0, y0, x1, y1 = box
    y0, y1 = max(0, y0 - 4), min(mt.H, y1 + 4)
    sub = Y[y0:y1, x0:x1]
    ink = ((sub - mt.box(sub, 3)) > 35) & (sub > 110)
    on = ink.sum(axis=1) > 1
    runs, y = [], 0
    while y < len(on):
        if on[y]:
            a = y
            gap = 0
            while y < len(on) and gap < 3:
                gap = 0 if on[y] else gap + 1
                y += 1
            runs.append([y0 + a, y0 + y - gap])
        else:
            y += 1
    return [r for r in runs if r[1] - r[0] >= 6], ink


def spec(movie):
    data = json.loads((SUBS / ('%s.json' % movie)).read_text(encoding='utf-8'))
    rows = np.load(mt.CACHE / ('%s_rows.npy' % movie))
    total = rows.shape[0]
    es, _ = mt.elementary(movie)
    live = [c for c in data['cards'] if not c.get('skip') and c.get('en')]
    peaks = {c['peak'] for c in live}
    frame = {}
    for n, buf in mt.frames(es, 0, total):
        if n in peaks:
            frame[n] = mt.planes(buf)[0]
    segments = []
    for c in live:
        x0, y0, x1, y1 = c['box']
        a, b = c['frames']
        kind = c['kind']
        Y = frame[c['peak']]
        runs, ink = text_rows(Y, c['box'])
        # Lines: where the Japanese lines really are (the scan may merge two lines into one band).
        en_lines = c['en'].split(chr(10))
        want = max(len(runs), len(c['lines']))
        if len(en_lines) == 1 and want > 1:
            en_lines = wrap_even(c['en'], want, SIZE[kind], WEIGHT[kind])
        top = runs[0][0] if runs else y0
        bottom = runs[-1][1] if runs else y1
        if len(runs) == len(en_lines):
            bands = [list(r) for r in runs]
        else:
            pitch = max((bottom - top) / len(en_lines), SIZE[kind] + 6)
            mid = (top + bottom) / 2
            first = mid - pitch * len(en_lines) / 2
            bands = [[round(first + pitch * i), round(first + pitch * (i + 1))] for i in range(len(en_lines))]
        lines = []
        for band, t in zip(bands, en_lines):
            lines.append({'band': band, 'en': t, 'align': 'center', 'x': 256, 'width': 420,
                          'size': SIZE[kind], 'weight': WEIGHT[kind]})
        lines[0]['ja'] = c['ja']
        # Background: captions on the black bar or a black screen are restored with black; otherwise from the
        # nearest frames without lettering, well clear of the fades, combined by per-pixel minimum.
        lo, hi = max(0, min(y0, top) - 6), min(mt.H, max(y1, bottom) + 6)
        around = Y[lo:hi, max(0, x0 - 20):min(mt.W, x1 + 20)]
        letters = mt.dilate(((around - mt.box(around, 3)) > 35) & (around > 110), 2)
        bg_level = float(np.median(around[~letters]))
        if bg_level < 28:
            refs = ['black']
        else:
            r0 = quiet(rows, lo, hi, a - 30, -1, 120, total)
            r1 = quiet(rows, lo, hi, b + 29, 1, 120, total)
            refs = [r for r in (r0, r1) if r is not None] or ['black']
        segments.append({'type': 'static', 'card': c['id'], 'frames': [a, b],
                         'box': [max(0, min(x0, 46) - 4), lo, min(mt.W, max(x1, 466) + 4), hi],
                         'refs': refs, 'combine': 'min', 'colour': [200, 128, 128], 'lines': lines,
                         'ink_rows': [[r0 - 2, r1 + 2] for r0, r1 in runs] or [[y0 - 2, y1 + 2]],
                         'bg_level': round(bg_level, 1)})
    out = {'movie': movie, 'note': 'Generated by tools/subtitle_spec.py from subs/%s.json; edit the cards, not this file.' % movie,
           'segments': segments}
    (mt.SPEC / ('%s.json' % movie)).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(movie, len(segments), 'segments', sum(1 for s in segments if s['refs'] == ['black']), 'on black')


def wrap_even(text, n, size, weight):
    f = ImageFont.truetype(mt.NOTO, size * 4)
    try:
        f.set_variation_by_axes([weight])
    except (OSError, AttributeError):
        pass
    words = text.split(' ')
    if n != 2 or len(words) < 2:
        return [text]
    best = min(range(1, len(words)), key=lambda k: max(f.getlength(' '.join(words[:k])), f.getlength(' '.join(words[k:]))))
    return [' '.join(words[:best]), ' '.join(words[best:])]


if __name__ == '__main__':
    cmd = sys.argv[1]
    for m in sys.argv[2:]:
        (cards if cmd == 'cards' else spec)(m)
