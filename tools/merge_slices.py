"""Merge translator slices into work/translation/en/encyclopedia.json and normalize shared formatting.

    python tools/merge_slices.py            # dry run: shows what would change
    python tools/merge_slices.py --write

Normalizations (house style for the mech stat block): "Source:" -> "Series:" (原作), one double space between
the Height and Weight fields.
"""
import json
import re
import sys
from ace_formats import ROOT, require

MAIN = ROOT / 'work/translation/en/encyclopedia.json'
SLICES = sorted((ROOT / 'work/translation/en/slices').glob('slice*.json'))


def normalize(text):
    text = re.sub(r'(?m)^(\s*)Source: ', r'\1Series: ', text)
    text = re.sub(r'(Height: [^\n]*?)\s{2,}(Weight:)', r'\1  \2', text)
    return text


def main():
    main_rows = {t['term']: t for t in json.loads(MAIN.read_text(encoding='utf-8'))}
    changes = 0
    for path in SLICES:
        for t in json.loads(path.read_text(encoding='utf-8')):
            base = main_rows[t['term']]
            require([p['ja'] for p in base['pages']] == [p['ja'] for p in t['pages']], 'Source text changed in ' + path.name)
            for p in t['pages']:
                p['en'] = normalize(p['en'])
            if t != base:
                changes += 1
            main_rows[t['term']] = t
    print('terms updated:', changes)
    if '--write' in sys.argv:
        MAIN.write_text(json.dumps(list(main_rows.values()), ensure_ascii=False, indent=1), encoding='utf-8')
        print('wrote', MAIN)


if __name__ == '__main__':
    main()
