"""Check the 4x HUD font; dry run by default, --write saves proofs and evidence."""
import argparse
import json
from pathlib import Path

from ace_formats import Font, ROOT, SOURCE_ISO, require, iso_files, bnd_entries, unpack
from verify_hud_warning import database, child, font_bytes, glyph_signature, BUNDLES
from ui_apply import patch_small_font
from ui_layout import HUD_STOCK_LABELS, hud_stock_text, load
from vwf_font import render
from texture_text import SPEC, apply_spec
from title_stamp import stamp_texture, TEXTURE


def leaf(name):
    return name.rsplit('\\', 1)[-1]


def packed(data):
    raw = unpack(data)
    return {e['name']: raw[e['offset']:e['offset'] + e['size']] for e in bnd_entries(raw)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iso', type=Path)
    ap.add_argument('--version', default='0.1.23')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    expected, fonts = {}, {}
    changed, copies = [], 0
    with open(SOURCE_ISO, 'rb') as original, (ROOT / 'work/output/ACE-EN-0.1.22.iso').open('rb') as prior:
        source, before = database(original), database(prior)
        for name in BUNDLES:
            stock_data = source.read(next(e for e in source.entries if leaf(e['name']) == name))
            old_data = before.read(next(e for e in before.entries if leaf(e['name']) == name))
            expected[name] = patch_small_font(*font_bytes(stock_data), 'hud13')
            stock, old, new = Font(*font_bytes(stock_data)), Font(*font_bytes(old_data)), Font(*expected[name])
            require((new.tw, new.th, new.psm, new.mode) == (512, 512, 44, 0), 'Wrong atlas format')
            require(old.clut == new.clut, 'HUD palette changed')
            for c in range(32, 127):
                a, b = old.glyph(chr(c)), new.glyph(chr(c))
                require(all(a[k] == b[k] for k in ('width', 'bearing', 'advance', 'pad')), 'Screen metrics changed')
                require(round((b['uv'][3] - b['uv'][1]) * new.th) == 52, 'Not a 4x glyph')
            for c in set(''.join(hud_stock_text(s) for s in HUD_STOCK_LABELS.values())):
                require(glyph_signature(stock, c) == glyph_signature(new, c), 'Warning glyph changed')
            for row in load('speakers')['rows']:
                require(old.width(row['en']) == new.width(row['en']), 'Speaker-name spacing changed')
            fonts[name] = new
        tex = source.read(next(e for e in source.entries if leaf(e['name']) == TEXTURE))
        spec = json.loads((SPEC / 't3105_tm2.json').read_text(encoding='utf-8'))
        _, artwork = apply_spec(tex, spec)
        title, _ = stamp_texture(tex, artwork, args.version)
        if args.iso:
            with args.iso.open('rb') as result:
                after = database(result)
                require([e['name'] for e in before.entries] == [e['name'] for e in after.entries], 'Resource list changed')
                for a, b in zip(before.entries, after.entries):
                    aa, bb = before.read(a), after.read(b)
                    if aa == bb:
                        continue
                    name = leaf(a['name'])
                    changed.append(a['name'])
                    if name in BUNDLES:
                        require(font_bytes(bb) == expected[name], 'Incorrect 4x HUD copy')
                        from dialogue_source import unnamed_bnd
                        require(unnamed_bnd(aa).keys() == unnamed_bnd(bb).keys(), 'HUD children changed')
                        for ident in unnamed_bnd(aa):
                            if ident not in (50071, 50051):
                                require(child(aa, ident) == child(bb, ident), 'Unrelated HUD data changed')
                        copies += 1
                    elif name == TEXTURE:
                        require(bb == title, 'Title version mismatch')
                    elif name in ('MenuTitle.csc', 'MenuTitleIntro.csc'):
                        ac, bc = packed(aa), packed(bb)
                        require(ac.keys() == bc.keys(), 'Title children changed')
                        for k in ac:
                            require(bc[k] == (title if leaf(k) == TEXTURE else ac[k]), 'Unrelated title data changed')
                    else:
                        raise ValueError('Unrelated resource changed: ' + a['name'])
                require(copies == 4, 'Expected all four HUD font copies')
                a, b = iso_files(prior)['/SLPS_253.94'], iso_files(result)['/SLPS_253.94']
                prior.seek(a['offset']); result.seek(b['offset'])
                require(prior.read(a['size']) == result.read(b['size']), 'Executable changed')
            old_report = json.loads((ROOT / 'work/output/ACE-EN-0.1.22.json').read_text())
            new_report = json.loads(args.iso.with_suffix('.json').read_text())
            require(old_report['movies'] == new_report['movies'], 'Movies changed')
    evidence = dict(version=args.version, iso=str(args.iso) if args.iso else None,
                    texels_per_unit=4, atlas=[512, 512], metrics_preserved=True,
                    warning_pixels_and_palette_preserved=True, hud_copies=copies,
                    changed_resources=changed, iso_comparison_passed=bool(args.iso),
                    runtime_verified=False,
                    runtime_check='Expanded PSMT4HH allocation: check speaker, warnings and surrounding HUD in gameplay.')
    print(json.dumps(evidence, indent=2))
    if args.write:
        out = ROOT / ('work/ui/hud-font-' + args.version)
        out.mkdir(parents=True, exist_ok=True)
        samples = ['Torres', 'Bright', 'Kouichirou Misumaru', 'Martian Successors']
        render(fonts['Fe1p.bnd'], samples, scale=4).save(out / 'font-4x.png')
        render(fonts['Fe1p.bnd'], ['Torres', 'Kouichirou Misumaru'], scale=4, native=True).save(out / 'font-native.png')
        render(fonts['Fe1p.bnd'], [hud_stock_text(s) for s in HUD_STOCK_LABELS.values()],
               scale=4, colour=(230,70,40)).save(out / 'warnings.png')
        (out / 'verification.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
