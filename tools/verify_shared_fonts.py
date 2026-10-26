"""Verify English-only fonts, shared GS placement and the scope of a completed ISO."""
import argparse
import json
import struct
from pathlib import Path

from ace_formats import Font, ROOT, SOURCE_ISO, bnd_entries, iso_files, require, u32, unpack
from dialogue_source import unnamed_bnd
from english_fonts import character, japanese, shared
from ui_layout import keep_chars, HUD_STOCK_LABELS, hud_stock_text
from verify_hud_warning import database, child, font_bytes, glyph_signature
from vwf_font import render
from title_stamp import TEXTURE, stamp_texture
from texture_text import SPEC, apply_spec
from font_upload import HUD_UPLOAD_CALLS, HUD_REFRESH_GATES, LINEAR_UPLOAD, SWIZZLED_UPLOAD, file_offset, jal, check_calls
from font_refresh import check_refresh


def leaf(name):
    return name.rsplit('\\', 1)[-1]


def named(data):
    raw = unpack(data)
    return {e['name']: raw[e['offset']:e['offset'] + e['size']] for e in bnd_entries(raw)}


def font_check(new, old):
    require(not any(japanese(character(c)) for c in new.map), 'Japanese glyph map remains')
    require(len(new.glyphs) == len(set(new.map.values())), 'Unreferenced glyph records remain')
    for c in range(32, 127):
        a, b = old.glyph(chr(c)), new.glyph(chr(c))
        require(b is not None, 'Missing ASCII glyph')
        require(all(a[k] == b[k] for k in ('bearing', 'width', 'advance', 'pad')), 'Text metrics changed')
        require(0 <= b['uv'][0] < b['uv'][2] <= 1 and 0 <= b['uv'][1] < b['uv'][3] <= 1,
                'Glyph outside atlas')


def verify(iso, version):
    baseline = ROOT / 'work/output/ACE-EN-0.1.28.iso'
    current = json.loads(iso.with_suffix('.json').read_text(encoding='utf-8'))
    version = version or current['version']
    prior = json.loads(baseline.with_suffix('.json').read_text())
    require(current['movies'] == prior['movies'] and not current['movies_without_lyrics'], 'Movies/lyrics changed')
    require(current['shared_ingame_font'], 'Shared font not enabled')
    expected, report = {}, None
    with SOURCE_ISO.open('rb') as source:
        db = database(source)
        for name in ('Fe1p.bnd', 'Fe2p.bnd'):
            b = db.read(next(e for e in db.entries if leaf(e['name']) == name))
            dc, dt = child(b, 50070), child(b, 50050)
            parts, report = shared(dc[:u32(dc, 4)], dt[:u32(dt, 0)], *font_bytes(b), keep_chars('hud13'))
            expected[name] = dict(zip((50070, 50050, 50071, 50051), parts))
            d, h = Font(*parts[:2]), Font(*parts[2:])
            require(d.pixels == h.pixels, 'Shared textures have different texels')
            require(d.mode == h.mode == 1 and d.psm == h.psm == 20, 'Shared format/transfer differs')
            require(h.clut == Font(*font_bytes(b)).clut, 'HUD palette changed')
            for label in HUD_STOCK_LABELS.values():
                for c in hud_stock_text(label):
                    require(glyph_signature(Font(*font_bytes(b)), c) == glyph_signature(h, c), 'Warning changed')
            for fo in (d, h):
                for c in range(32, 127):
                    g = fo.glyph(chr(c))
                    require(round((g['uv'][3] - g['uv'][1]) * fo.th) == fo.cell * 4, 'Not 4x')
        raw = db.read(next(e for e in db.entries if leaf(e['name']) == TEXTURE))
        _, art = apply_spec(raw, json.loads((SPEC / 't3105_tm2.json').read_text(encoding='utf-8')))
        title, _ = stamp_texture(raw, art, version)
    copies, checked_fonts, changed = 0, 0, []
    with baseline.open('rb') as previous, iso.open('rb') as result:
        before, after = database(previous), database(result)
        require([e['name'] for e in before.entries] == [e['name'] for e in after.entries], 'Resource list changed')
        for a, b in zip(before.entries, after.entries):
            aa, bb = before.read(a), after.read(b)
            if aa == bb:
                continue
            name = leaf(a['name']); changed.append(a['name'])
            if name in expected:
                require(unnamed_bnd(aa).keys() == unnamed_bnd(bb).keys(), 'HUD children changed')
                for ident in unnamed_bnd(aa):
                    actual = child(bb, ident)
                    if ident in expected[name]:
                        wanted = expected[name][ident]
                        require(actual == wanted + bytes(-len(wanted) % 32), 'Incorrect shared font child')
                    else:
                        require(actual == child(aa, ident), 'Unrelated HUD child changed')
                for ci, ti in ((50070, 50050), (50071, 50051)):
                    old_c, old_t = child(aa, ci), child(aa, ti)
                    font_check(Font(expected[name][ci], expected[name][ti]),
                               Font(old_c[:u32(old_c, 4)], old_t[:u32(old_t, 0)]))
                    checked_fonts += 1
                copies += 1
            elif name == TEXTURE:
                require(bb == title, 'Incorrect title version')
            elif name.endswith('.csc'):
                ac, bc = named(aa), named(bb)
                require(ac.keys() == bc.keys(), 'Menu children changed')
                for key in ac:
                    if ac[key] == bc[key]:
                        continue
                    part = leaf(key)
                    require(part in ('f005.ccm', 'f005.tm2', 'f010.ccm', 'f010.tm2', TEXTURE),
                            'Unrelated menu child changed: ' + key)
                    if part == TEXTURE:
                        require(bc[key] == title, 'Incorrect bundled title')
                    elif part.endswith('.ccm'):
                        tex = key[:-4] + '.tm2'
                        font_check(Font(bc[key], bc[tex]), Font(ac[key], ac[tex])); checked_fonts += 1
            elif name in ('f005.ccm', 'f005.tm2', 'f010.ccm', 'f010.tm2'):
                if name.endswith('.ccm'):
                    tn = a['name'][:-4] + '.tm2'
                    at = before.read(next(e for e in before.entries if e['name'] == tn))
                    bt = after.read(next(e for e in after.entries if e['name'] == tn))
                    font_check(Font(bb, bt), Font(aa, at)); checked_fonts += 1
            else:
                raise ValueError('Unrelated resource changed: ' + a['name'])
        require(copies == 4, 'Expected four shared-font bundles')
        old_files, new_files = iso_files(previous), iso_files(result)
        require(old_files.keys() == new_files.keys(), 'Disc files changed')
        for name in old_files:
            if name == '/DATA.BIN' or name.endswith('.PSS'):
                continue  # build.py readbacks check each movie against its unchanged hash above.
            a, b = old_files[name], new_files[name]
            previous.seek(a['offset']); result.seek(b['offset'])
            aa, bb = previous.read(a['size']), result.read(b['size'])
            if name == '/SLPS_253.94':
                offset = 0x2a64d8 - 0x100000 + 0x80
                require(u32(aa, offset) == 0xc00 and u32(bb, offset) == 0x2600, 'Wrong fixed GS base')
                allowed = bytearray(aa); struct.pack_into('<I', allowed, offset, 0x2600)
                for address in HUD_UPLOAD_CALLS:
                    at = file_offset(address)
                    require(u32(aa, at) == jal(LINEAR_UPLOAD) and u32(bb, at) == jal(SWIZZLED_UPLOAD),
                            'Wrong HUD startup upload call')
                    struct.pack_into('<I', allowed, at, jal(SWIZZLED_UPLOAD))
                for address, instruction in HUD_REFRESH_GATES.items():
                    at = file_offset(address)
                    require(u32(aa, at) == instruction and u32(bb, at) == 0, 'Wrong HUD frame refresh gate')
                    struct.pack_into('<I', allowed, at, 0)
                from dialogue_buffer import patch as patch_dialogue_buffer, verify as verify_dialogue_buffer
                patch_dialogue_buffer(allowed, {})
                report['operator_drawing_buffer'] = verify_dialogue_buffer(bb)
                require(bb == allowed, 'Unrelated executable change')
                report['hud_upload_transfers'] = check_calls(bb, expected['Fe1p.bnd'][50051])
                report['hud_frame_refresh'] = check_refresh(bb, expected['Fe1p.bnd'][50050])
                require(struct.unpack_from('<4I', bb, offset - 8) == (0x2600, 0x3ff4, 0x2600, 0x3fff),
                        'Shared base/palettes differ')
            else:
                require(aa == bb, 'Unrelated disc file changed')
    out = ROOT / ('work/ui/hud-speaker-' + version); out.mkdir(exist_ok=True, parents=True)
    render(h, ['Bright', 'Torres', 'Drake Soldier', 'UCE', 'Leprechaun'], scale=4).save(out / 'shared-hud.png')
    render(d, ['The UCE betrayed us once the test succeeded,'], scale=2).save(out / 'shared-dialogue.png')
    report.update(version=version, iso=str(iso), hud_copies=copies, fonts_checked=checked_fonts,
                  movies_and_lyrics_unchanged=True, changed_resources=changed, iso_comparison_passed=True)
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('iso', type=Path)
    ap.add_argument('--version', help='Defaults to the ISO build report version')
    args = ap.parse_args()
    verify(args.iso, args.version)
