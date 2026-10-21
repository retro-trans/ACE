"""Check carrier-panel texture boundaries and optional ISO changes. Dry run; --write saves proofs."""
import argparse
import json
import struct
from pathlib import Path
from PIL import Image
from ace_formats import ROOT, SOURCE_ISO, iso_files, require
from texture_text import SPEC, apply_spec, decode
from title_stamp import TEXTURE, stamp_texture
from verify_title_stamp import database, leaf, children
from verify_movie_scope import range_hash

PANEL = 't0403.tm2'


def preview(atlas):
    # b043.mnb object 32: fixed label strip, stretched value area, fixed right border.
    result = Image.new('RGBA', (200, 167))
    for a, b, x0, x1 in ((0, 97, .1587, 94.2618), (97, 175, 94.2618, 94.1005),
                         (175, 200, 94.1005, 118.103)):
        piece = atlas.transform((b-a, 167), Image.EXTENT, (x0, .8986, x1, 167.3242), Image.BILINEAR)
        result.paste(piece, (a, 0))
    bg = Image.new('RGBA', result.size, (0, 22, 30, 255))
    bg.alpha_composite(result)
    return bg.resize((600, 501), Image.LANCZOS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='0.1.25')
    parser.add_argument('--iso', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    expected, copies = {}, {PANEL: 0, TEXTURE: 0}
    with open(SOURCE_ISO, 'rb') as f:
        db = database(f)
        for name in (PANEL, TEXTURE):
            original = db.read(next(e for e in db.entries if leaf(e['name']) == name))
            spec = json.loads((SPEC / (name.replace('.', '_') + '.json')).read_text(encoding='utf-8'))
            expected[name], artwork = apply_spec(original, spec)
            if name == TEXTURE:
                expected[name], _ = stamp_texture(original, artwork, args.version)
            else:
                panel_spec = spec
                before, after = decode(original), decode(expected[name])
                require(before.crop((94, 0, 119, 167)).tobytes() == after.crop((94, 0, 119, 167)).tobytes(),
                        'Lettering entered the stretched value strip/right border')
                for i in (0, 2, 3, 5, 7, 9):
                    label = spec['labels'][i]
                    require(label['box'][2] <= 90 and not any(label.get('grow', [0, 0])), 'Label crosses seam')
        mesh = db.read(next(e for e in db.entries if leaf(e['name']) == 'b043.mnb'))
        uv = struct.unpack_from('<16f', mesh, 0x2f50)
        require([round(v*256) for v in uv] == [0,1,0,167,94,1,94,167,94,1,94,167,118,1,118,167],
                'Unexpected carrier panel UVs')
    changed = []
    prior_path = ROOT / 'work/output/ACE-EN-0.1.24.iso'
    with prior_path.open('rb') as old:
        db = database(old)
        old_panel = decode(db.read(next(e for e in db.entries if leaf(e['name']) == PANEL)))
        require(old_panel.crop((120, 0, 256, 256)).tobytes() == after.crop((120, 0, 256, 256)).tobytes(),
                'Left-side upgrade labels changed')
        if args.iso:
            with args.iso.open('rb') as new:
                current = database(new)
                require([e['name'] for e in db.entries] == [e['name'] for e in current.entries], 'Resource list changed')
                for ae, be in zip(db.entries, current.entries):
                    aa, bb = db.read(ae), current.read(be)
                    if aa == bb:
                        continue
                    name = leaf(ae['name'])
                    changed.append(ae['name'])
                    if name in expected:
                        require(bb == expected[name], 'Incorrect texture: ' + name)
                        copies[name] += 1
                    else:
                        require(name.endswith('.csc'), 'Unrelated resource changed: ' + name)
                        ac, bc = children(aa), children(bb)
                        require(ac.keys() == bc.keys(), 'Bundle child list changed')
                        for key in ac:
                            short = leaf(key)
                            require(bc[key] == expected.get(short, ac[key]), 'Unrelated bundled resource changed: ' + key)
                            if short in expected:
                                copies[short] += 1
                require(all(n >= 2 for n in copies.values()), 'Missing standalone/packed texture copies')
                af, bf = iso_files(old), iso_files(new)
                require(af.keys() == bf.keys(), 'Disc file list changed')
                for name, entry in af.items():
                    if name == '/DATA.BIN':
                        continue
                    other = bf[name]
                    require(entry['size'] == other['size'], 'Disc file size changed: ' + name)
                    require(range_hash(old, entry['offset'], entry['size']) ==
                            range_hash(new, other['offset'], other['size']), 'Other disc file changed: ' + name)
    result = dict(version=args.version, iso=str(args.iso) if args.iso else None,
                  changed_resources=changed, copies=copies, stretch_strip_clean=True,
                  mesh_uvs_verified=True, left_upgrade_labels_unchanged=True,
                  iso_comparison_passed=bool(args.iso), runtime_verified=False,
                  panel_labels=[panel_spec['labels'][i] for i in (0,2,3,5,7,9)])
    # Only English UI metadata is included in the saved report.
    from strip_jp import strip
    result = strip(result)
    print(json.dumps(result, indent=1))
    if args.write:
        out = ROOT / ('work/ui/carrier-panel-' + args.version)
        out.mkdir(parents=True, exist_ok=True)
        preview(old_panel).save(out / 'before.png')
        preview(after).save(out / 'after.png')
        (out / 'verification.json').write_text(json.dumps(result, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
