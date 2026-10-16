"""Check (and wrap) translated UI groups in work/translation/en/ui/*.json.

Each group names its font and limits (measured from the Japanese by tools/ui_prepare.py):
  f010   menu font with the HD English set (as in the Terminology database)
  f005   unit/weapon/part-name font; rebuilt with only the stock glyphs the English still uses plus English
  hud13  lock-on / radio-speaker font (resource 50071), rebuilt the same way
Rows: "\\n" is a hard break; longer lines are wrapped at the group width; the result must not exceed the group's
line count; bytes include the digit widening of the menu widget copy routine (EE 0x212040) for f010.
Format codes (%d, %1d, %s) and tokens must match the Japanese.

    python tools/ui_layout.py check [group ...]
"""
import json
import re
import sys
from ace_formats import ROOT
from vwf_font import add_english, reclaim

DIR = ROOT / 'work/translation/en/ui'
TOKEN = re.compile(r'<[a-z]+\([^)]*\)>|%%|%[-+0 #]*\d*[a-z]')
_fonts = {}
# Fe1p/Fe2p child 50140/5 already contains English in full-width CP932.
# These rows are not translation groups, but still use the rebuilt HUD font.
HUD_STOCK_LABELS = {2: 'AREA OVER', 22: 'CAUTION', 23: 'ON AIR', 24: 'MISSILE', 25: 'ERROR'}


def hud_stock_text(text):
    return ''.join('\u3000' if c == ' ' else chr(ord(c) + 0xfee0) for c in text)


def groups():
    return sorted(p.stem for p in DIR.glob('*.json') if not p.name.endswith('.en.json'))


def load(name):
    return json.loads((DIR / ('%s.json' % name)).read_text(encoding='utf-8'))


def keep_chars(font_name):
    """Non-ASCII glyphs needed by translated groups and existing English HUD labels."""
    chars = set()
    if font_name == 'hud13':
        chars.update(''.join(hud_stock_text(s) for s in HUD_STOCK_LABELS.values()))
    for g in groups():
        data = load(g)
        if data['font'] == font_name:
            for r in data['rows']:
                chars |= {c for c in (r.get('en') or '') if ord(c) > 126}
    return chars


def font(name):
    if name not in _fonts:
        if name == 'f010':
            from encyclopedia_layout import font as menu_font
            _fonts[name] = menu_font()
        else:
            from ui_prepare import stock_fonts
            f = stock_fonts()[name]
            start = reclaim(f, keep_chars(name))
            add_english(f, start=start)
            _fonts[name] = f
    return _fonts[name]


def width(fo, text):
    return sum(fo.advance(c) for c in TOKEN.sub('', text) if fo.glyph(c) is not None)


def wrap(fo, text, limit):
    out = []
    for src in text.split('\n'):
        line = ''
        for w in src.split(' '):
            cand = (line + ' ' + w) if line else w
            if width(fo, cand) <= limit or not line:
                line = cand
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def stored(group, row):
    fo = font(group['font'])
    return '\n'.join(wrap(fo, row['en'], group['limits']['width']))


def game_bytes(group, text):
    raw = text.encode('cp932')
    return len(raw) + (sum(0x30 <= b <= 0x39 for b in raw) if group['font'] == 'f010' else 0)


def problems(group, row):
    en = row.get('en') or ''
    if not en:
        return ['untranslated']
    out = []
    fo = font(group['font'])
    lim = group['limits']
    if sorted(TOKEN.findall(en)) != sorted(TOKEN.findall(row['ja'])):
        out.append('format codes/tokens differ: %s vs %s' % (TOKEN.findall(en), TOKEN.findall(row['ja'])))
    missing = sorted({c for c in TOKEN.sub('', en) if c != '\n' and fo.glyph(c) is None})
    if missing:
        out.append('no glyph for %s' % ''.join(missing))
    if group['font'] != 'f010' and any(ord(c) > 126 for c in en):
        out.append('use ASCII only in this font (non-ASCII keeps a stock glyph: %s)' % ''.join(sorted({c for c in en if ord(c) > 126})))
    lines = wrap(fo, en, lim['width'])
    if len(lines) > lim['lines']:
        out.append('%d lines (max %d)' % (len(lines), lim['lines']))
    for l in lines:
        if width(fo, l) > lim['width']:
            out.append('line too wide (%d > %d): %r' % (width(fo, l), lim['width'], l))
    n = game_bytes(group, '\n'.join(lines))
    if n > lim['bytes']:
        out.append('%d bytes (max %d)' % (n, lim['bytes']))
    return out


def main():
    want = sys.argv[2:] or groups()
    total = done = bad = 0
    for g in want:
        data = load(g)
        for row in data['rows']:
            total += 1
            p = problems(data, row)
            if p != ['untranslated']:
                done += 1
            if p and p != ['untranslated']:
                bad += 1
                print('PROBLEM %s id %s: %s' % (g, row['id'], '; '.join(p)))
    print('%d rows, %d translated, %d problem(s)' % (total, done, bad))


if __name__ == '__main__':
    main()
