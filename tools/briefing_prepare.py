"""Create briefing translation files work/translation/en/briefing/fNNN.json from MenuFree.csc (which holds every
mission table, including the extra missions f080/f081). Existing files are never overwritten.

    python tools/briefing_prepare.py
"""
import json
import re
from ace_formats import bnd_entries, fmg_read, unpack
from briefing_layout import DIR

NAME = re.compile(r'fmg\\f(0\d\d)\.fmg$')


def main():
    from dialogue_source import open_data
    f, db = open_data()
    e = next(x for x in db.entries if x['name'].endswith('MenuFree.csc'))
    bundle = unpack(db.read(e))
    f.close()
    DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for c in bnd_entries(bundle):
        m = NAME.search(c['name'])
        if not m:
            continue
        t = m.group(1)
        rows = fmg_read(bundle[c['offset']:c['offset'] + c['size']])
        path = DIR / ('f%s.json' % t)
        if path.exists():
            continue
        data = {'table': t, 'dialogue_file': 'work/translation/en/dialogue/m%s.json' % t,
                'rows': [{'id': i, 'ja': v, 'en': '', 'notes': ''} for i, v in sorted(rows.items()) if v]}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        n += 1
    print('tables written', n)


if __name__ == '__main__':
    main()
