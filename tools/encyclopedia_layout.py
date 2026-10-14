"""Wrap and paginate English Terminology (f205) text with the VWF font, and check it against measured limits.

Limits (all proven by the stock data, see docs/encyclopedia.md):
  * line width   <= 440 units  (widest Japanese line: 442)
  * lines/page   <= 8          (Japanese pages use 8; one uses 9)
  * bytes/page   <= 390        (largest Japanese page: 391 bytes; ASCII digits count 2 because the widget copy
                                routine widens them to fullwidth codes, and '%' is doubled for the printf call)
  * titles       <= 27 bytes and <= 230 units (largest Japanese title)

Text conventions in work/translation/en/encyclopedia.json:
  * "\\n" is a hard line break; everything else is wrapped automatically at word boundaries.
  * Leading spaces on a line are kept as a hanging indent for its wrapped continuation lines.
  * Each source page starts a new game page; an overflowing page continues on extra pages (term*100+n).

    python tools/encyclopedia_layout.py check            # report overflow per term
    python tools/encyclopedia_layout.py preview [term..] # PNG proofs in work/ui/encyclopedia/
    ACE_TRANSLATION=work/translation/en/slices/slice1.json python tools/encyclopedia_layout.py check
"""
import json
import os
import sys
from ace_formats import ROOT, SOURCE_ISO, Font, bnd_child, bnd_entries, read_iso_file, require, unpack
from vwf_font import add_english, render

LINE_WIDTH, PAGE_LINES, PAGE_BYTES = 440, 8, 390
TITLE_WIDTH, TITLE_BYTES = 230, 27
TRANSLATION = ROOT / 'work/translation/en/encyclopedia.json'
if os.environ.get('ACE_TRANSLATION'):
    TRANSLATION = ROOT / os.environ['ACE_TRANSLATION']

_font = None


def font():
    global _font
    if _font is None:
        data = read_iso_file(SOURCE_ISO, '/DATA.BIN')
        e = next(e for e in bnd_entries(data) if e['name'].endswith('MenuCampaign.csc'))
        bundle = unpack(data[e['offset']:e['offset'] + e['size']])
        _font = Font(bnd_child(bundle, 'f010.ccm'), bnd_child(bundle, 'f010.tm2'))
        add_english(_font)
    return _font


def game_bytes(text):
    """Bytes the widget buffer holds for ``text``: the printf output (one byte per '%') with ASCII digits
    widened to two-byte fullwidth codes by the copy routine at EE 0x212040."""
    raw = text.encode('cp932')
    return len(raw) + sum(0x30 <= b <= 0x39 for b in raw)


def stored(text):
    """Text as stored in the FMG: the page is used as a printf format string (EE 0x210c30)."""
    return text.replace('%', '%%')


def missing_glyphs(text):
    f = font()
    return sorted({c for c in text if c != '\n' and f.glyph(c) is None})


def wrap(text, width=LINE_WIDTH):
    f = font()
    lines = []
    for src in text.split('\n'):
        indent = src[:len(src) - len(src.lstrip(' '))]
        words = src.strip(' ').split(' ')
        line = indent
        for w in words:
            candidate = (line + ' ' + w) if line.strip() else indent + w
            if f.width(candidate) <= width or not line.strip():
                line = candidate
            else:
                lines.append(line.rstrip())
                line = indent + w
        lines.append(line.rstrip())
    return lines


def paginate(text):
    """Split one source page into game pages of <= PAGE_LINES lines and <= PAGE_BYTES bytes."""
    pages, cur = [], []
    for line in wrap(text):
        trial = cur + [line]
        if cur and (len(trial) > PAGE_LINES or game_bytes('\n'.join(trial)) > PAGE_BYTES):
            pages.append(cur)
            cur = [line]
        else:
            cur = trial
    if cur:
        pages.append(cur)
    # Drop leading blank lines on continuation pages.
    pages = [p[next((i for i, l in enumerate(p) if l.strip()), 0):] if n else p for n, p in enumerate(pages)]
    return pages


def term_pages(term):
    """Return the list of game pages (each a list of lines) for one translated term."""
    out = []
    for page in term['pages']:
        out += paginate(page['en'])
    return out


def load():
    return json.loads(TRANSLATION.read_text(encoding='utf-8'))


def problems(terms):
    found = []
    f = font()
    for t in terms:
        title = t.get('title_en') or ''
        if not title:
            found.append((t['term'], 'untranslated title'))
        else:
            if missing_glyphs(title):
                found.append((t['term'], 'title glyphs missing: %s' % missing_glyphs(title)))
            if f.width(title) > TITLE_WIDTH or game_bytes(title) > TITLE_BYTES:
                found.append((t['term'], 'title too long: %d units, %d bytes' % (f.width(title), game_bytes(title))))
        for p in t['pages']:
            if not p.get('en'):
                found.append((t['term'], 'untranslated page %d' % p['id']))
                continue
            if missing_glyphs(p['en']):
                found.append((t['term'], 'page %d glyphs missing: %s' % (p['id'], missing_glyphs(p['en']))))
            for line in wrap(p['en']):
                if f.width(line) > LINE_WIDTH:
                    found.append((t['term'], 'page %d unbreakable line: %r' % (p['id'], line)))
        if all(p.get('en') for p in t['pages']) and len(term_pages(t)) > 99:
            found.append((t['term'], 'more than 99 pages'))
    return found


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    terms = load()
    if cmd == 'check':
        for t in terms:
            if not all(p.get('en') for p in t['pages']):
                continue
            pages = term_pages(t)
            print('%3d %-28s src pages %d -> game pages %d (lines %s, bytes %s)' % (
                t['term'], (t.get('title_en') or '')[:28], len(t['pages']), len(pages),
                [len(p) for p in pages], [game_bytes('\n'.join(p)) for p in pages]))
        bad = problems(terms)
        for b in bad:
            print('PROBLEM', *b)
        print('%d problem(s)' % len(bad))
    elif cmd == 'preview':
        want = {int(a) for a in sys.argv[2:]}
        out = ROOT / 'work/ui/encyclopedia'
        out.mkdir(parents=True, exist_ok=True)
        for t in terms:
            if want and t['term'] not in want or not all(p.get('en') for p in t['pages']):
                continue
            for n, page in enumerate(term_pages(t), 1):
                render(font(), [t['title_en'], ''] + page + [''] * (PAGE_LINES - len(page)),
                       width=LINE_WIDTH + 8).save(out / ('term%02d_page%d.png' % (t['term'], n)))
        print('previews in', out)


if __name__ == '__main__':
    main()
