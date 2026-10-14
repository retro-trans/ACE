"""Briefings, debriefings and mission labels (menu tables f001-f081): wrap and check translated rows.

Table layout per mission (fNNN.fmg in MenuCampaign.csc, MenuFree.csc and standalone; byte-identical copies):
  1 mission name, 2-4 objective / defeat / secret-objective labels, 100+ briefing, 200+ debriefing,
  300 failure line.

Tokens occur inside the text: <cs(n)>...<ce()> colour a phrase; <pic(n)> shows a picture; <mk(x,y,a,b)> and
<ar(...)> draw map markers and arrows; <pt(...)>. They are parsed by the same tokenizer engine as in-mission
dialogue (registration at EE 0x1fd04c), with a separate handler set. Translators keep the exact token sequence
(same tokens, same order) and wrap the English counterpart of a coloured phrase in <cs(n)>...<ce()>.

Limits (Japanese maxima in brackets). The briefing text buffer is not located; after two in-mission buffers
turned out to be sized for the Japanese (operator window, 2026-10-14), every byte limit here equals the Japanese
maximum:
  name       1 line,  200 units, 27 bytes   [195 units, 27 bytes]
  objective  2 lines, 200 units, 39 bytes   [201 units, 39 bytes]
  briefing / debriefing / failure  2 lines, 440 units, 89 visible bytes  [450 units, 89 bytes]

Translation files: work/translation/en/briefing/fNNN.json {table, mission, rows: [{id, ja, en, notes}]}
    python tools/briefing_layout.py check [NNN ...]
"""
import json
import re
import sys
from ace_formats import ROOT
from encyclopedia_layout import font

DIR = ROOT / 'work/translation/en/briefing'
TOKEN = re.compile(r'<[a-z]+\([^)]*\)>')
LIMITS = {'name': (1, 200, 27), 'objective': (2, 200, 39), 'text': (2, 440, 89)}


def kind(ident):
    return 'name' if ident == 1 else 'objective' if ident < 100 else 'text'


def visible(text):
    return TOKEN.sub('', text)


def width(text):
    f = font()
    return sum(f.advance(c) for c in visible(text) if f.glyph(c) is not None)


def wrap(text, limit):
    """Most balanced split into at most two lines at a space outside tokens; explicit newlines are kept."""
    if '\n' in text or width(text) <= limit:
        return text.split('\n')
    spaces = [m.start() for m in re.finditer(' ', text) if not any(t.start() < m.start() < t.end() for t in TOKEN.finditer(text))]
    best = None
    for s in spaces:
        a, b = text[:s], text[s + 1:]
        score = (max(width(a), width(b)), -width(a))
        if best is None or score < best[0]:
            best = (score, [a, b])
    return best[1] if best else [text]


def stored(ident, en):
    lines, limit, _ = LIMITS[kind(ident)]
    return '\n'.join(wrap(en, limit))


def problems(row):
    en = row.get('en') or ''
    if not en:
        return ['untranslated']
    out = []
    if TOKEN.findall(en) != TOKEN.findall(row['ja']):
        out.append('token sequence differs from Japanese: %s vs %s' % (TOKEN.findall(en), TOKEN.findall(row['ja'])))
    f = font()
    src = visible(row['ja'])
    missing = sorted({c for c in visible(en) if c != '\n' and f.glyph(c) is None and c not in src})
    if missing:
        out.append('no glyph for %s' % ''.join(missing))
    if '%' in en:
        out.append('avoid "%" (text may pass through printf)')
    max_lines, limit, max_bytes = LIMITS[kind(row['id'])]
    lines = wrap(en, limit)
    if len(lines) > max_lines:
        out.append('%d lines (max %d)' % (len(lines), max_lines))
    for l in lines:
        if width(l) > limit:
            out.append('line too wide (%d > %d units): %r' % (width(l), limit, visible(l)))
    raw = visible('\n'.join(lines)).encode('cp932')
    n = len(raw) + sum(0x30 <= b <= 0x39 for b in raw)
    if n > max_bytes:
        out.append('%d bytes (max %d)' % (n, max_bytes))
    return out


def load(table):
    return json.loads((DIR / ('f%s.json' % table)).read_text(encoding='utf-8'))


def tables():
    """Tables with a translation file, minus those marked ``excluded`` (f000: digit/symbol table)."""
    return sorted(p.stem[1:] for p in DIR.glob('f*.json') if not p.name.endswith('.en.json')
                  and not json.loads(p.read_text(encoding='utf-8')).get('excluded'))


def main():
    total = done = bad = 0
    for t in sys.argv[2:] or tables():
        for row in load(t)['rows']:
            total += 1
            p = problems(row)
            if p != ['untranslated']:
                done += 1
            if p and p != ['untranslated']:
                bad += 1
                print('PROBLEM f%s id %d: %s' % (t, row['id'], '; '.join(p)))
    print('%d rows, %d translated, %d problem(s)' % (total, done, bad))


if __name__ == '__main__':
    main()
