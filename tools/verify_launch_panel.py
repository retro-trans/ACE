"""Verify launch-panel label boundaries and optional ISO differences from 0.1.25. --write saves proofs."""
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

PANEL = 't0802.tm2'


def preview(atlas):
    result = Image.new('RGBA', (172, 112), (0,22,30,255))
    for top, y0, y1, pieces in (
        (0, 3.323, 54.0185, [(0,107,.389,107.425), (107,124,107.425,91.633), (124,172,91.633,139.807)]),
        (61,55.1885,106.4245, [(0,93,.128,93.036), (93,124,93.036,91.021), (124,172,91.021,139.195)])):
        for a,b,x0,x1 in pieces:
            tile = atlas.transform((b-a,51), Image.EXTENT, (x0,y0,x1,y1), Image.BILINEAR)
            result.alpha_composite(tile, (a,top))
    return result.resize((688,448), Image.LANCZOS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    expected, copies, uv_checks = {}, {PANEL:0, TEXTURE:0}, []
    with open(SOURCE_ISO,'rb') as f:
        db = database(f)
        for name in (PANEL,TEXTURE):
            raw = db.read(next(e for e in db.entries if leaf(e['name']) == name))
            spec = json.loads((SPEC/(name.replace('.','_')+'.json')).read_text(encoding='utf-8'))
            expected[name], artwork = apply_spec(raw,spec)
            if name == TEXTURE:
                expected[name], _ = stamp_texture(raw,artwork,'0.1.26')
            else:
                source, after = decode(raw), decode(expected[name])
                require(source.size == (256,128),'Unexpected atlas size')
                require(source.crop((91,0,140,108)).tobytes() == after.crop((91,0,140,108)).tobytes(),
                        'Changed stretch/continuation strip or percent sign')
                for i,right in ((0,86),(2,85)):
                    require(spec['labels'][i]['box'][2] <= right and not any(spec['labels'][i].get('grow',[0,0])),
                            'Label exceeds the fixed strip')
        for name,offsets in (('b081.mnb',[(0x23a0,107.425,91.633),(0x2550,93.036,91.021)]),
                             ('b083.mnb',[(0x3120,96.799,91.845),(0x32c0,88.087,140.101)])):
            mesh = db.read(next(e for e in db.entries if leaf(e['name'])==name))
            for offset,left,right in offsets:
                uv = struct.unpack_from('<16f',mesh,offset)
                require(abs(uv[4]*256-left)<.002 and abs(uv[8]*256-right)<.002,'Unexpected panel UVs')
                uv_checks.append(dict(mesh=name,offset=offset,uv_pixels=[round(v*(256 if i%2==0 else 128),4) for i,v in enumerate(uv)]))
    changed = []
    prior_path = ROOT/'work/output/ACE-EN-0.1.25.iso'
    with prior_path.open('rb') as old:
        db = database(old)
        old_panel = decode(db.read(next(e for e in db.entries if leaf(e['name'])==PANEL)))
        require(old_panel.crop((140,0,256,128)).tobytes()==after.crop((140,0,256,128)).tobytes(),
                'Armor/Repair Resources artwork changed')
        if args.iso:
            with args.iso.open('rb') as new:
                current = database(new)
                require([e['name'] for e in db.entries]==[e['name'] for e in current.entries],'Resource list changed')
                for ae,be in zip(db.entries,current.entries):
                    aa,bb = db.read(ae),current.read(be)
                    if aa==bb:
                        continue
                    name=leaf(ae['name']); changed.append(ae['name'])
                    if name in expected:
                        require(bb==expected[name],'Incorrect texture: '+name); copies[name]+=1
                    else:
                        require(name.endswith('.csc'),'Unrelated resource changed: '+name)
                        ac,bc=children(aa),children(bb)
                        require(ac.keys()==bc.keys(),'Bundle children changed')
                        for key in ac:
                            short=leaf(key)
                            require(bc[key]==expected.get(short,ac[key]),'Unrelated bundled resource changed: '+key)
                            if short in expected: copies[short]+=1
                require(all(n>=2 for n in copies.values()),'Missing texture copies')
                af,bf=iso_files(old),iso_files(new)
                require(af.keys()==bf.keys(),'Disc file list changed')
                for name,entry in af.items():
                    if name=='/DATA.BIN': continue
                    other=bf[name]
                    require(entry['size']==other['size'],'Disc file size changed')
                    require(range_hash(old,entry['offset'],entry['size'])==range_hash(new,other['offset'],other['size']),
                            'Other disc file changed: '+name)
    result=dict(version='0.1.26',iso=str(args.iso) if args.iso else None,changed_resources=changed,copies=copies,
                uv_checks=uv_checks,stretch_strips_clean=True,other_atlas_labels_unchanged=True,
                iso_comparison_passed=bool(args.iso),runtime_verified=False)
    print(json.dumps(result,indent=1))
    if args.write:
        folder=ROOT/'work/ui/launch-panel-0.1.26';folder.mkdir(parents=True,exist_ok=True)
        preview(old_panel).save(folder/'before.png');preview(after).save(folder/'after.png')
        (folder/'verification.json').write_text(json.dumps(result,indent=1),encoding='utf-8')


if __name__=='__main__':
    main()
