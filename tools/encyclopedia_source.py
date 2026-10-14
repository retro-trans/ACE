"""Export the Terminology database (f205.fmg) to a local working file.

The table exists in MenuCampaign.csc, MenuFree.csc and as a standalone resource; the copies are compared and must
match. Titles are ids 1..99; description pages are ``term * 100 + page``. The game counts pages by probing
consecutive ids from ``term*100+1`` (EE 0x2760d0), so a term may use more pages than the Japanese did.

    python tools/encyclopedia_source.py   # writes work/source/encyclopedia_ja.json (git-ignored)
"""
import json
from ace_formats import ROOT, SOURCE_ISO, bnd_child, bnd_entries, fmg_read, read_iso_file, require, unpack

BUNDLES = ('MenuCampaign.csc', 'MenuFree.csc')
OUT = ROOT / 'work/source/encyclopedia_ja.json'


def load(data=None):
    data = data or read_iso_file(SOURCE_ISO, '/DATA.BIN')
    entries = bnd_entries(data)
    copies = {}
    for name in BUNDLES:
        e = next(e for e in entries if e['name'].endswith(name))
        copies[name] = fmg_read(bnd_child(unpack(data[e['offset']:e['offset'] + e['size']]), 'f205.fmg'))
    e = next(e for e in entries if e['name'].endswith('fmg\\f205.fmg'))
    copies['standalone'] = fmg_read(data[e['offset']:e['offset'] + e['size']])
    first = copies[BUNDLES[0]]
    require(all(c == first for c in copies.values()), 'f205 copies differ')
    return first


def structure(rows):
    terms = {}
    for ident, text in rows.items():
        if text is None:
            continue
        if ident < 100:
            terms.setdefault(ident, {'title': None, 'pages': {}})['title'] = text
        else:
            term, page = divmod(ident, 100)
            terms.setdefault(term, {'title': None, 'pages': {}})['pages'][page] = text
    return terms


def main():
    rows = load()
    terms = structure(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out = [{'term': t, 'title': v['title'], 'pages': [{'id': t * 100 + p, 'ja': v['pages'][p]} for p in sorted(v['pages'])]}
           for t, v in sorted(terms.items())]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print('terms', len(out), 'pages', sum(len(t['pages']) for t in out), '->', OUT)


if __name__ == '__main__':
    main()
