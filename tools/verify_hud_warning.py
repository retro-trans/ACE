"""Check stock HUD warning glyphs and unchanged English glyphs; optionally verify a built ISO.

Without an ISO, checks the proposed font rebuild. --write saves reconstructed previews and a report.
"""
import argparse
import json
from pathlib import Path

from ace_formats import Font, ROOT, SOURCE_ISO, fmg_read, iso_files, require, u32
from build import DataBin, HUD_CCM, HUD_TM2
from dialogue_source import unnamed_bnd
from ui_apply import patch_small_font
from ui_layout import HUD_STOCK_LABELS, hud_stock_text
from vwf_font import render

BUNDLES = ('Fe1p.bnd', 'Fe2p.bnd')


def database(stream):
    rec = iso_files(stream)['/DATA.BIN']
    return DataBin(stream, rec['offset'], rec['size'])


def child(data, ident):
    at, size = unnamed_bnd(data)[ident]
    return data[at:at + size]


def font_bytes(data):
    ccm, tm2 = child(data, HUD_CCM), child(data, HUD_TM2)
    return ccm[:u32(ccm, 4)], tm2[:u32(tm2, 0)]


def glyph_signature(font, char):
    """Compare actual palette indices and screen metrics, independent of atlas placement."""
    g = font.glyph(char)
    require(g is not None, 'Missing glyph: ' + ascii(char))
    x0, y0, x1, y1 = [round(v * size) for v, size in zip(g['uv'], (font.tw, font.th) * 2)]
    pixels = b''.join(bytes(font.pixels[y * font.tw + x0:y * font.tw + x1]) for y in range(y0, y1))
    return (g['bearing'], g['width'], g['advance'], g['pad'], x1 - x0, y1 - y0, pixels)


def check_font(stock, previous, current):
    chars = set(''.join(hud_stock_text(s) for s in HUD_STOCK_LABELS.values()))
    for char in chars:
        require(current.map[current.code(char)] != current.map[current.code('?')], 'Warning still uses fallback')
        require(glyph_signature(stock, char) == glyph_signature(current, char), 'Stock warning glyph changed')
    for code in range(32, 127):
        require(glyph_signature(previous, chr(code)) == glyph_signature(current, chr(code)),
                'Existing English glyph changed: ' + chr(code))
    require(previous.clut == current.clut, 'HUD palette changed')
    for i in range(5):
        require(stock.clut[i * 4:i * 4 + 4] == current.clut[i * 4:i * 4 + 4], 'Stock alpha changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', nargs='?', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    previous_path = ROOT / 'work/output/ACE-EN-0.1.18.iso'
    expected, previews = {}, {}
    with open(SOURCE_ISO, 'rb') as source, previous_path.open('rb') as old:
        original, before = database(source), database(old)
        for name in BUNDLES:
            raw = original.read(next(e for e in original.entries if e['name'].endswith(name)))
            previous = before.read(next(e for e in before.entries if e['name'].endswith(name)))
            rows = fmg_read(child(child(raw, 50140), 5))
            require({i: v for i, v in rows.items() if v} ==
                    {i: hud_stock_text(s) for i, s in HUD_STOCK_LABELS.items()}, 'Stock HUD labels changed')
            expected[name] = patch_small_font(*font_bytes(raw), 'hud13')
            current = Font(*expected[name])
            stock, prior = Font(*font_bytes(raw)), Font(*font_bytes(previous))
            check_font(stock, prior, current)
            previews[name] = current
        changed = []
        if args.iso:
            with args.iso.open('rb') as new:
                after = database(new)
                require([e['name'] for e in before.entries] == [e['name'] for e in after.entries],
                        'Resource list changed')
                for a, b in zip(before.entries, after.entries):
                    old_raw, new_raw = before.read(a), after.read(b)
                    if old_raw == new_raw:
                        continue
                    name = a['name'].rsplit('\\', 1)[-1]
                    require(name in BUNDLES, 'Unrelated resource changed: ' + name)
                    changed.append(a['name'])
                    require(font_bytes(new_raw) == expected[name], 'Unexpected rebuilt font')
                    old_kids, new_kids = unnamed_bnd(old_raw), unnamed_bnd(new_raw)
                    require(old_kids.keys() == new_kids.keys(), 'HUD bundle child list changed')
                    for ident in old_kids:
                        if ident not in (HUD_CCM, HUD_TM2):
                            require(child(old_raw, ident) == child(new_raw, ident),
                                    'Unrelated HUD child changed: %s/%s' % (name, ident))
                require({name.rsplit('\\', 1)[-1] for name in changed} == set(BUNDLES),
                        'Not both HUD fonts replaced')
                a, b = iso_files(old)['/SLPS_253.94'], iso_files(new)['/SLPS_253.94']
                old.seek(a['offset']); new.seek(b['offset'])
                require(old.read(a['size']) == new.read(b['size']), 'Executable changed')
    report = dict(iso=args.iso.name if args.iso else None, previous=previous_path.name,
                  restored_labels=list(HUD_STOCK_LABELS.values()),
                  stock_glyph_pixels_and_metrics_preserved=True, ascii_glyphs_unchanged=True,
                  changed_resources=changed, comparison_passed=bool(args.iso))
    print(json.dumps(report, indent=2))
    if args.write:
        out = ROOT / 'work/ui/hud-warning-0.1.19'
        out.mkdir(parents=True, exist_ok=True)
        for name, fo in previews.items():
            render(fo, [hud_stock_text(s) for s in HUD_STOCK_LABELS.values()],
                   scale=4, colour=(230, 70, 40), bg=(45, 16, 12)).save(out / (name + '.png'))
        (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
