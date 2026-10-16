"""Verify 0.1.18 changes only four menu textures, including their packed copies.

Also reconstructs controller panels from the encoded textures and checks the
actual b032 mesh UV bounds. Pass --write to save previews and the report.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from PIL import Image
from ace_formats import ROOT, bnd_entries, iso_files, unpack, require
from build import DataBin
import texture_text as tt

NAMES = {'t0300.tm2', 't0301.tm2', 't0302.tm2', 't0303.tm2'}


def database(stream):
    record = iso_files(stream)['/DATA.BIN']
    return DataBin(stream, record['offset'], record['size'])


def leaf(name):
    return name.rsplit('\\', 1)[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--previous', type=Path, default=ROOT / 'work/output/ACE-EN-0.1.17.iso')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    expected, specs = {}, {}
    with tt.SPEC.joinpath('t0302_tm2.json').open(encoding='utf-8') as f:
        panel = json.load(f)['panels'][0]
    from dialogue_source import open_data
    source, original = open_data()
    try:
        for entry in original.entries:
            name = leaf(entry['name'])
            if name in NAMES:
                spec = json.loads((tt.SPEC / (name.replace('.', '_') + '.json')).read_text(encoding='utf-8'))
                specs[name] = spec
                expected[name], _ = tt.apply_spec(original.read(entry), spec)
            elif name == 'b032.mnb':
                mesh = original.read(entry)
        # Both controller modes use the same continuation UV rectangle.
        for at in (0x4e0, 0x5e0):
            uv = [round(v * 512) for v in struct.unpack_from('<8f', mesh, at)]
            require(uv == [196, 405, 505, 405, 196, 346, 505, 346], 'Controller mesh UVs changed')
        require(panel['pieces'][1] == dict(box=[196, 346, 505, 405], at=[512, 0], rotate=-90),
                'Panel continuation does not match actual mesh UVs')
    finally:
        source.close()
    copies = {name: 0 for name in NAMES}
    changed = []
    with args.previous.open('rb') as old, args.iso.open('rb') as new:
        before, after = database(old), database(new)
        require([e['name'] for e in before.entries] == [e['name'] for e in after.entries], 'Resource list changed')
        for a, b in zip(before.entries, after.entries):
            raw_a, raw_b = before.read(a), after.read(b)
            if raw_a == raw_b:
                continue
            name = leaf(a['name'])
            changed.append(a['name'])
            if name in NAMES:
                require(raw_b == expected[name], 'Wrong standalone texture: ' + name)
                copies[name] += 1
                continue
            require(name.endswith('.csc') and '\\menu\\' in a['name'].lower(), 'Unrelated resource changed: ' + name)
            aa, bb = unpack(raw_a), unpack(raw_b)
            ea = {e['name']: aa[e['offset']:e['offset'] + e['size']] for e in bnd_entries(aa)}
            eb = {e['name']: bb[e['offset']:e['offset'] + e['size']] for e in bnd_entries(bb)}
            require(ea.keys() == eb.keys(), 'Packed resource list changed')
            for child in ea:
                short = leaf(child)
                if short in NAMES:
                    require(eb[child] == expected[short], 'Wrong packed texture: ' + child)
                    copies[short] += 1
                else:
                    require(ea[child] == eb[child], 'Unrelated packed resource changed: ' + child)
        # The executable must remain untouched by this texture-only fix.
        for path in ('/SLPS_253.94',):
            ao, bo = iso_files(old)[path], iso_files(new)[path]
            old.seek(ao['offset']); new.seek(bo['offset'])
            require(old.read(ao['size']) == new.read(bo['size']), 'Executable changed')
    require(all(count >= 2 for count in copies.values()), 'Missing standalone/packed replacement')
    for name in ('t0300.tm2', 't0301.tm2'):
        labs = [lab for lab in specs[name]['labels'] if lab['en'].strip()]
        require([lab['box'][1] for lab in labs] == [11, 51, 91], 'Difficulty vertical positions differ')
    report = dict(iso=args.iso.name, previous=args.previous.name, changed_resources=changed,
                  texture_copies=copies, all_other_data_resources_identical=True,
                  executable_identical=True, controller_mesh_uvs_verified=True,
                  difficulty_label_shift_y=5,
                  textures={name: hashlib.sha256(raw).hexdigest() for name, raw in expected.items()})
    print(json.dumps(report, indent=2))
    if args.write:
        out = ROOT / 'work/ui/menu-fixes-0.1.18'
        out.mkdir(parents=True, exist_ok=True)
        for name, raw in expected.items():
            im = tt.decode(raw)
            if specs[name].get('panels'):
                im = tt.assemble_panel(im, specs[name]['panels'][0])
            else:
                im = im.crop((0, 0, 190, 120))
            im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(out / (name + '.verified.png'))
        (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
