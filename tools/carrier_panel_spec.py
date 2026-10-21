"""Keep carrier-info labels inside the mesh's fixed-width left strip. Dry run unless --write."""
import argparse
import json
from ace_formats import ROOT, require
from strip_jp import strip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'work/translation/en/textures/t0403_tm2.json'
    spec = json.loads(path.read_text(encoding='utf-8'))
    # b043.mnb object 32 stretches atlas x=94.1005..94.2618 across the value column.
    # A two-pixel margin also keeps shadow/filtering away from that strip.
    for index, old, new, right in ((0, 'Carrier Info', 'Carrier Info', 90),
                                  (2, 'Carrier Name', 'Carrier', 86),
                                  (3, 'Squad Name', 'Squad', 86),
                                  (5, 'Units', 'Units', 86),
                                  (7, 'Repair Res.', 'Repair Res.', 86),
                                  (9, 'Repair Eff.', 'Repair Eff.', 86)):
        label = spec['labels'][index]
        require(label['en'] in (old, new), 'Unexpected label at index %d' % index)
        label['en'] = new
        if index == 0:
            # Erase the complete original title even though the English drawing box is narrower.
            label['erase_box'] = [21, 4, 94, 24]
        label['box'][2] = right
        label.pop('grow', None)
        label['align'] = 'left'
        print('%s -> %s: box %s, no horizontal growth' % (old, new, label['box']))
    if args.write:
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        path.with_name('t0403_tm2.en.json').write_text(
            json.dumps(strip(spec), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
