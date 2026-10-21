"""Verify title version branding, unchanged artwork, and optional ISO differences from 0.1.20.

Dry-run verification by default; --write saves a reconstructed title preview and report.
"""
import argparse
import json
from pathlib import Path

from ace_formats import ROOT, SOURCE_ISO, bnd_entries, iso_files, require, unpack
from build import DataBin
from texture_text import SPEC, apply_spec, decode
from title_stamp import TEXTURE, LAYOUT, patch_layout, preview, stamp_texture


def database(stream):
    r = iso_files(stream)['/DATA.BIN']
    return DataBin(stream, r['offset'], r['size'])


def leaf(name):
    return name.rsplit('\\', 1)[-1]


def children(data):
    raw = unpack(data)
    return {e['name']: raw[e['offset']:e['offset'] + e['size']] for e in bnd_entries(raw)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--iso', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    spec = json.loads((SPEC / 't3105_tm2.json').read_text(encoding='utf-8'))
    expected = {}
    with open(SOURCE_ISO, 'rb') as src:
        original = database(src)
        tex = original.read(next(e for e in original.entries if leaf(e['name']) == TEXTURE))
        old_layout = original.read(next(e for e in original.entries if leaf(e['name']) == LAYOUT))
    base, im = apply_spec(tex, spec)
    expected[TEXTURE], stamp = stamp_texture(tex, im, args.version)
    expected[LAYOUT] = patch_layout(old_layout)
    # Quantization must not alter any existing pixel, palette entry or header.
    before, after = decode(base), decode(expected[TEXTURE])
    count = 0
    for y in range(before.height):
        for x in range(before.width):
            if before.getpixel((x, y)) != after.getpixel((x, y)):
                require(any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in stamp['atlas_bounds']),
                        'Existing title artwork changed')
                count += 1
    require(count > 0, 'Title stamp is empty')
    require(base[:32] == expected[TEXTURE][:32] and base[32 + 512 * 512:] == expected[TEXTURE][32 + 512 * 512:],
            'Title texture header or palette changed')
    copies = {TEXTURE: 0, LAYOUT: 0}
    changed = []
    if args.iso:
        with (ROOT / 'work/output/ACE-EN-0.1.20.iso').open('rb') as old, args.iso.open('rb') as new:
            a, b = database(old), database(new)
            require([e['name'] for e in a.entries] == [e['name'] for e in b.entries], 'Resource list changed')
            for ae, be in zip(a.entries, b.entries):
                aa, bb = a.read(ae), b.read(be)
                if aa == bb:
                    continue
                name = leaf(ae['name'])
                changed.append(ae['name'])
                if name in expected:
                    require(bb == expected[name], 'Unexpected title resource: ' + name)
                    copies[name] += 1
                else:
                    require(name.endswith('.csc') and '\\menu\\' in ae['name'],
                            'Unrelated resource changed: ' + name)
                    ac, bc = children(aa), children(bb)
                    require(ac.keys() == bc.keys(), 'Bundle child list changed')
                    for child, body in ac.items():
                        short = leaf(child)
                        if short in expected:
                            # Packed layout has different stock metadata from the standalone copy.
                            # Preserve its own bytes, changing only the two copyright bounds.
                            wanted = patch_layout(body) if short == LAYOUT else expected[short]
                            require(bc[child] == wanted, 'Wrong packed title resource: ' + ae['name'] + ':' + child)
                            copies[short] += 1
                        else:
                            require(body == bc[child], 'Unrelated bundled resource changed: ' + child)
            require(all(n >= 2 for n in copies.values()), 'Missing standalone or bundled title copy')
            fa, fb = iso_files(old)['/SLPS_253.94'], iso_files(new)['/SLPS_253.94']
            old.seek(fa['offset']); new.seek(fb['offset'])
            require(old.read(fa['size']) == new.read(fb['size']), 'Executable changed')
        report = json.loads(args.iso.with_suffix('.json').read_text(encoding='utf-8'))
        prior = json.loads((ROOT / 'work/output/ACE-EN-0.1.20.json').read_text(encoding='utf-8'))
        require(report['version'] == args.version and report['title_stamp'] == stamp, 'Wrong version/report stamp')
        require(report['movies'] == prior['movies'], 'Movie hashes changed')
    result = dict(version=args.version, iso=args.iso.name if args.iso else None,
                  stamp=stamp, changed_pixels=count, existing_artwork_preserved=True,
                  changed_resources=changed, copies=copies, iso_comparison_passed=bool(args.iso))
    print(json.dumps(result, indent=2))
    if args.write:
        out = ROOT / ('work/ui/title-stamp-' + args.version)
        out.mkdir(parents=True, exist_ok=True)
        screen = preview(expected[TEXTURE], expected[LAYOUT])
        screen.resize((1024, 896)).save(out / 'title-preview.png')
        screen.crop((24, 364, 512, 448)).resize((976, 168)).save(out / 'footer-preview.png')
        (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
