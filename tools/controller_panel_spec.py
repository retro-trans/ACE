"""Repair controller split-atlas labels and difficulty alignment. Dry run unless --write."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for name in ('t0300_tm2', 't0301_tm2'):
        path = ROOT / ('work/translation/en/textures/' + name + '.json')
        spec = json.loads(path.read_text(encoding='utf-8'))
        for label, old_top in (('Rookie', 6), ('Pilot', 46), ('Ace', 86)):
            lab = next(l for l in spec['labels'] if l['en'] == label)
            assert lab['box'][1] in (old_top, old_top + 5)
            lab['box'][1] = old_top + 5
            lab['box'][3] = old_top + 27
        print(name + ': lower all three labels by 5 texture pixels')
        if args.write:
            path.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for name in ('t0302_tm2', 't0303_tm2'):
        path = ROOT / ('work/translation/en/textures/' + name + '.json')
        spec = json.loads(path.read_text(encoding='utf-8'))
        # Horizontal rows provide the screen y-coordinate; rotated rows retain
        # the correct wording. Their full strips are NOT drawn by the game.
        right = [lab for lab in spec['labels'] if lab.get('note', '').startswith('right-column label:')]
        rotated = [lab for lab in spec['labels'] if lab.get('vertical') and lab.get('en', '').strip()]
        if spec.get('panels'):
            print(name + ': already prepared')
            continue
        assert len(right) == len(rotated) == 7, name
        labels = []
        for row, words in zip(right, rotated):
            # Spec order matches (shoulders, face buttons, stick); confirm that
            # the old erase note actually names this translation.
            assert "was '%s'" % words['en'] in row['note'], (row, words)
            y0, y1 = row['box'][1], row['box'][3]
            lab = dict(box=[430, y0, 542, y1], en=words['en'], align='center',
                       height=21, color=[205, 206, 207])
            labels.append(lab)
            words['en'] = ' '
            row['note'] = 'Erase source label before lettering the assembled panel.'
        # b032.mnb child 0, semi-auto UVs at file 0x5c0/0x5e0:
        # main (1.715, .256)..(511.744, 308.91);
        # continuation (196.234,346.23)..(504.888,404.552), rotated clockwise.
        spec['panels'] = [dict(size=[571, 309], pieces=[
            dict(box=[0, 0, 512, 309], at=[0, 0]),
            dict(box=[196, 346, 505, 405], at=[512, 0], rotate=-90)], labels=labels)]
        print(name + ': ' + ', '.join(lab['en'] for lab in labels))
        if args.write:
            path.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
