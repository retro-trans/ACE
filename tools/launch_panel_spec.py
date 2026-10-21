"""Keep launch resources/repair headings clear of the stretched atlas strips. Dry run unless --write."""
import argparse
import json
from ace_formats import ROOT, require
from strip_jp import strip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'work/translation/en/textures/t0802_tm2.json'
    spec = json.loads(path.read_text(encoding='utf-8'))
    for i, name, right, source in ((0, 'Resources', 86, [23,7,57,24]),
                                   (2, 'Repair Eff.', 85, [22,59,90,76])):
        lab = spec['labels'][i]
        require(lab['en'] == name, 'Unexpected label')
        lab['erase_box'] = source
        lab['box'][2] = right
        lab.pop('grow', None)
        print('%s: draw %s, erase %s, no growth' % (name, lab['box'], source))
    if args.write:
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        path.with_name('t0802_tm2.en.json').write_text(json.dumps(strip(spec), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
