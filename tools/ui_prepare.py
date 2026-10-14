"""Create translation files for the remaining UI tables (everything except dialogue, briefings and Terminology).

    python tools/japanese_inventory.py      # first (reads the newest build)
    python tools/ui_prepare.py

Groups come from work/source/japanese_inventory.json and are named by their table. Each file records the font
that draws it (decided by glyph coverage: the stock fonts are subsets containing exactly the characters their
text needs) and limits measured from the Japanese with that font's stock metrics:
  lines  = most lines in any row of the group
  width  = widest Japanese line in the group (font units)
  bytes  = largest Japanese row (bytes)

Lock-on labels (one-row tables in InGameNNN.bnd) are merged into one file keyed by their Japanese text.
Existing English is never overwritten.
"""
import json
import re
import struct
from ace_formats import ROOT, Font, bnd_child, u32, unpack

DIR = ROOT / 'work/translation/en/ui'
TOKEN = re.compile(r'<[a-z]+\([^)]*\)>|#c(\[[0-9A-Fa-f]{6}\])?')
# Inventory locations -> group name and font. 'units' covers f201 and f251 (identical tables).
GROUPS = [
    ('weapons', 'f005', lambda w: 'fmg\\f252.fmg' in w or w.endswith('f252.fmg')),
    ('weapons_f206', 'f010', lambda w: w.endswith('f206.fmg')),
    ('units', 'f005', lambda w: w.endswith(('f201.fmg', 'f251.fmg'))),
    ('parts', 'f005', lambda w: w.endswith('f250.fmg')),
    ('memcard', 'f010', lambda w: w.endswith('f204.fmg')),
    ('help', 'f010', lambda w: w.endswith('f200.fmg')),
    ('desc', 'f010', lambda w: w.endswith('f202.fmg')),
    ('modes', 'f010', lambda w: w.endswith('f100.fmg')),
    ('common', 'f010', lambda w: w.endswith('CommonMessage.fmg')),
    ('speakers', 'hud13', lambda w: 'Fe1p.bnd' in w or 'Fe2p.bnd' in w),
]


def stock_fonts():
    from dialogue_source import open_data, unnamed_bnd
    f, db = open_data()
    e = next(x for x in db.entries if x['name'].endswith('MenuCampaign.csc'))
    b = unpack(db.read(e))
    fonts = {n: Font(bnd_child(b, n + '.ccm'), bnd_child(b, n + '.tm2')) for n in ('f005', 'f010')}
    e = next(x for x in db.entries if x['name'].endswith('Fe1p.bnd'))
    d = db.read(e)
    k = unnamed_bnd(d)
    o, _ = k[50071]
    ccm = d[o:o + u32(d, o + 4)]
    o, _ = k[50051]
    fonts['hud13'] = Font(ccm, d[o:o + u32(d, o)])
    f.close()
    return fonts


def limits(rows, font):
    lines = widths = size = 0
    for v in rows:
        vis = TOKEN.sub('', v)
        ls = vis.split('\n')
        lines = max(lines, len(ls))
        widths = max([widths] + [sum(font.advance(c) for c in l if font.glyph(c)) for l in ls])
        size = max(size, len(v.encode('cp932')))
    return {'lines': lines, 'width': widths, 'bytes': size}


def main():
    inv = json.loads((ROOT / 'work/source/japanese_inventory.json').read_text(encoding='utf-8'))
    fonts = stock_fonts()
    DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    lockon = {}
    for g in inv:
        where = g['where']
        leaf = [w.split('@')[0].split(':')[-1] for w in where]
        if all(re.search(r'InGame\d+\.bnd$', w.split('@')[0]) for w in where):
            if len(g['rows']) == 1:
                for v in g['rows'].values():
                    lockon.setdefault(v, []).extend(where)
            continue  # multi-row InGame tables are the (stale) dialogue originals
        name = next((n for n, _, test in GROUPS if any(test(w) for w in leaf)), None)
        if name is None:
            print('UNGROUPED', where[:3], len(g['rows']))
            continue
        variant = name
        k = 2
        while variant in out:
            variant = '%s_v%d' % (name, k)
            k += 1
        font = next(f for n, f, _ in GROUPS if n == name)
        out[variant] = {'group': variant, 'font': font, 'where': where,
                        'limits': limits(g['rows'].values(), fonts[font]),
                        'rows': [{'id': int(i), 'ja': v, 'en': '', 'notes': ''} for i, v in g['rows'].items()]}
    out['lockon'] = {'group': 'lockon', 'font': 'hud13', 'where': sorted({w for v in lockon.values() for w in v}),
                     'limits': limits(lockon.keys(), fonts['hud13']),
                     'note': 'One-row lock-on label tables in InGameNNN.bnd; keyed by Japanese text (id is a sequence number).',
                     'rows': [{'id': n, 'ja': v, 'en': '', 'notes': ''} for n, v in enumerate(sorted(lockon), 1)]}
    for name, data in out.items():
        path = DIR / ('%s.json' % name)
        if path.exists():
            old = {r['ja']: r for r in json.loads(path.read_text(encoding='utf-8'))['rows']}
            for r in data['rows']:
                if r['ja'] in old and old[r['ja']].get('en'):
                    r.update({k: v for k, v in old[r['ja']].items() if k != 'id'})
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        print('%-14s %-6s rows %4d  limits %s  x%d' % (name, data['font'], len(data['rows']), data['limits'], len(data['where'])))


if __name__ == '__main__':
    main()
