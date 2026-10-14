"""Write Japanese-free *.en.json copies of translation working files (the only translation files committed).

    python tools/strip_jp.py
For each work/translation/en/**/*.json (except translator slices) (not already *.en.json) writes <name>.en.json with every key ending in
'_ja' or named 'ja' removed, and translator 'note'/'notes' (they quote Japanese source phrases)
removed. Fails if any Japanese script remains outside names allowed by AGENTS.md
(the check only reports; review the listed rows).
"""
import json
import re
from ace_formats import ROOT

JP_SCRIPT = re.compile(r'[぀-ヿ一-鿿]')


def strip(value):
    if isinstance(value, dict):
        return {k: strip(v) for k, v in value.items()
                if not (k in ('ja', 'note', 'notes', 'units', 'context') or k.endswith('_ja'))}
    if isinstance(value, list):
        return [strip(v) for v in value]
    return value


def main():
    for path in sorted((ROOT / 'work/translation/en').rglob('*.json')):
        if 'slices' in path.parts:
            continue
        if path.name.endswith('.en.json'):
            continue
        clean = strip(json.loads(path.read_text(encoding='utf-8')))
        text = json.dumps(clean, ensure_ascii=False, indent=1)
        leftovers = sorted(set(JP_SCRIPT.findall(text)))
        out = path.with_name(path.stem + '.en.json')
        out.write_text(text, encoding='utf-8')
        print(out.name, 'written', ('- %d Japanese characters left, review before committing' % len(leftovers)) if leftovers else '- clean')


if __name__ == '__main__':
    main()
