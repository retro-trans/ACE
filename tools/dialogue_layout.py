"""Wrap and check translated in-mission dialogue against the measured window limits.

Limits:
  * at most 2 lines per row in the main radio window (<on()> ... <off()>; Japanese never uses more), and exactly
    1 line in the operator window (<op()> ... <ed()>): the Japanese never breaks a line there (2,477 rows), and a
    two-line message in it hangs the game (found in play: mission 1 row 62, build 0.1.8),
  * line width <= 400 units in the dialogue font (widest Japanese line 408, nearly all <= 383),
  * visible bytes <= 128 per row. The message object keeps the typed text in a 132-byte buffer
    (offset 0x24-0xa7, cleared per row by EE 0x2366e0) and appends without a bounds check (EE 0x237b14).
    Tokens <...> are not copied; '#c[RRGGBB]' colour codes and line breaks are.

Rows are stored as  <prefix tokens> + English + <suffix tokens>; tokens never occur inside the Japanese text,
so translators write only the visible English. "\\n" in the English forces a break; otherwise the wrapper picks
the most balanced two-line split.

Translation files: work/translation/en/dialogue/mNNN.json  {mission, context, rows: [{id, ja, en, notes}]}

    python tools/dialogue_layout.py check [mission ...]
    python tools/dialogue_layout.py preview <mission> [id ...]   # PNGs in work/ui/dialogue/
"""
import json
import re
import sys
from ace_formats import ROOT, require
from vwf_font import add_english, render

# 128 fits the 132-byte typing buffer found in the code, but the operator window crashed on a buffer that is not
# that one, so the radio window is held to what is proven in play (93 bytes, mission 1 row 15; Japanese max 83).
LINE_WIDTH, MAX_LINES, MAX_BYTES = 400, 2, 93
# Operator window: a row of 57 visible bytes crashed the game in play (mission 1 row 69, build 0.1.10), 56 bytes
# played fine and the Japanese never exceeds 52; 54 keeps a margin under the proven size.
OP_MAX_BYTES = 54
# Operator rows with a <cs(n)> speaker colour: the colour code shares the same buffer (about 10 bytes), so the text
# is held to the Japanese maximum for these rows, 46 bytes. A 53-byte row stalled mission 3's script (row 21,
# build 0.1.19; found by bisecting with diagnostic builds).
OP_CS_MAX_BYTES = 46
# Objective and failure labels (rows 1-9 without tokens) are drawn on the HUD; their buffer is not located, so they
# are held to the Japanese maximum (28 bytes).
OBJECTIVE_MAX_BYTES = 28
DIR = ROOT / 'work/translation/en/dialogue'
EDGE = re.compile(r'^((?:<[a-z]+\([^)]*\)>)*)(.*?)((?:<[a-z]+\([^)]*\)>)*)$', re.S)

_font = None


def font():
    global _font
    if _font is None:
        from dialogue_source import open_data, ingame_font
        f, db = open_data()
        e = next(x for x in db.entries if x['name'].endswith('Fe1p.bnd'))
        _font = ingame_font(db.read(e))
        f.close()
        add_english(_font)
    return _font


def split(ja):
    m = EDGE.match(ja)
    return m.group(1), m.group(2), m.group(3)


def width(text):
    f = font()
    return sum(f.advance(c) for c in text if f.glyph(c) is not None)


def windows(rows):
    """{row id: 'on' | 'op' | None}: the message window each row is shown in. A row opening <on()> or <op()>
    starts that window; it stays open for the following rows until a row ending it with <off()> or <ed()>."""
    out, win = {}, None
    for r in sorted(rows, key=lambda r: r['id']):
        ja = r.get('ja') or ''
        if '<on(' in ja:
            win = 'on'
        elif '<op(' in ja:
            win = 'op'
        out[r['id']] = win
        if '<off()>' in ja or '<ed()>' in ja:
            win = None
    return out


def max_lines(window):
    return 1 if window == 'op' else MAX_LINES


def wrap(text, lines=MAX_LINES):
    """Most balanced split into at most ``lines`` lines; explicit newlines are kept."""
    if '\n' in text:
        return text.split('\n')
    if lines == 1 or width(text) <= LINE_WIDTH:
        return [text]
    words = text.split(' ')
    best = None
    for k in range(1, len(words)):
        a, b = ' '.join(words[:k]), ' '.join(words[k:])
        score = (max(width(a), width(b)), -width(a))
        if best is None or score < best[0]:
            best = (score, [a, b])
    return best[1] if best else [text]


def stored(ja, en, window=None, scale_typing=False):
    prefix, src, suffix = split(ja)
    if scale_typing:
        # <sp(N)> is the delay per typed character (EE 0x2370f0 stores it; the typewriter at 0x237790 types one
        # character each time the frame-time accumulator passes it). Keep the English typing time equal to the
        # Japanese one, so the mission script's timing stays as in the original.
        ja_chars = len(re.sub(r'#c(\[[0-9A-Fa-f]{6}\])?|\s', '', src))
        en_chars = len(en.replace('\n', ''))
        if en_chars > ja_chars > 0:
            prefix = re.sub(r'<sp\((\d+)\)>', lambda m: '<sp(%d)>' % max(1, round(int(m.group(1)) * ja_chars / en_chars)),
                            prefix)
    return prefix + '\n'.join(wrap(en, max_lines(window))) + suffix


def visible_bytes(text):
    return len(text.encode('cp932'))


def problems(row, window=None):
    out = []
    en = row.get('en') or ''
    _, src, _ = split(row['ja'])
    if not src.strip():
        return [] if not en else ['source row has no visible text; leave en empty']
    if not en:
        return ['untranslated']
    f = font()
    missing = sorted({c for c in en if c != '\n' and f.glyph(c) is None and c not in src})
    if missing:
        out.append('no glyph for %s' % ''.join(missing))
    if re.search(r'<[a-z]+\(', en):
        out.append('control token inside English (write visible text only)')
    lines = wrap(en, max_lines(window))
    if len(lines) > max_lines(window):
        out.append('%d lines (max %d in the %s window)' % (len(lines), max_lines(window), window or 'radio'))
    for l in lines:
        if width(l) > LINE_WIDTH:
            out.append('line too wide (%d units): %r' % (width(l), l))
    n = visible_bytes('\n'.join(lines))
    limit = OP_MAX_BYTES if window == 'op' else MAX_BYTES
    if window == 'op' and '<cs(' in row['ja']:
        limit = OP_CS_MAX_BYTES
    if row['id'] < 10 and not split(row['ja'])[0]:
        limit = OBJECTIVE_MAX_BYTES        # objective / failure labels drawn on the HUD
    if n > limit:
        out.append('%d visible bytes (max %d in the %s window)' % (n, limit, window or 'radio'))
    return out


def load(mission):
    return json.loads((DIR / ('m%s.json' % mission)).read_text(encoding='utf-8'))


def missions():
    """Mission ids with a translation file, minus files marked ``excluded`` (debug/test text)."""
    out = []
    for p in sorted(DIR.glob('m*.json')):
        if p.name.endswith('.en.json'):
            continue
        if not json.loads(p.read_text(encoding='utf-8')).get('excluded'):
            out.append(p.stem[1:])
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'check':
        total = bad = done = 0
        for m in sys.argv[2:] or missions():
            rows = load(m)['rows']
            win = windows(rows)
            for row in rows:
                total += 1
                p = problems(row, win[row['id']])
                if p != ['untranslated']:
                    done += 1
                if p and p != ['untranslated']:
                    bad += 1
                    print('PROBLEM m%s id %d: %s' % (m, row['id'], '; '.join(p)))
        print('%d rows, %d translated, %d problem(s)' % (total, done, bad))
    elif cmd == 'preview':
        m = sys.argv[2]
        want = {int(a) for a in sys.argv[3:]}
        out = ROOT / 'work/ui/dialogue'
        out.mkdir(parents=True, exist_ok=True)
        rows = [r for r in load(m)['rows'] if r.get('en') and (not want or r['id'] in want)]
        lines = []
        for r in rows:
            lines += wrap(r['en']) + ['']
        render(font(), lines[:40], scale=3, width=LINE_WIDTH + 8).save(out / ('m%s.png' % m))
        print('preview', out / ('m%s.png' % m))


if __name__ == '__main__':
    main()
