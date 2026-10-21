"""Variable-width, 4x-resolution (HD) English glyphs for the menu fonts.

The game's text renderer is already proportional: every CCM glyph has its own width and advance. The stock
fonts, however, carry only a few wide Latin letters (lowercase ``a`` advances 13 units). This module rasterizes
a complete printable-ASCII set from Noto Sans JP (SIL Open Font License, see THIRD_PARTY_NOTICES.md), packs it
into unused atlas rows and remaps the ASCII codes (and the fullwidth digits the widget copy routine substitutes
for ASCII digits) to the new glyphs.

HD: the glyph renderer (EE 0x1c8bd8-0x1c8ce8) sizes each sprite from the glyph's *metrics* - pen + bearing to
pen + width, one cell high, all times the text scale - and takes the texture coordinates separately from the
float UV rectangle. The English glyphs are therefore stored at SCALE (4) texels per unit: an English letter
covers 4x4 texels per screen unit, so it stays sharp when an emulator renders above native resolution, while
the metrics (and therefore every line width and page layout) are those of a 1x design. The 11 unused CLUT
entries (5-15) receive extra alpha levels so the anti-aliasing has a 16-step ramp; entries 0-4, which the stock
glyphs use, are unchanged. Original glyph records and pixels are kept; only the code map, glyph list, spare
atlas rows and spare palette entries change.

    python tools/vwf_font.py --preview      # writes work/ui/vwf/*.png from the stock MenuCampaign f010
"""
import argparse
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ace_formats import ROOT, Font, require

NOTO = Path(r'C:\Windows\Fonts\NotoSansJP-VF.ttf')
ASCII = [chr(c) for c in range(0x20, 0x7f)]
FULLWIDTH_DIGITS = [chr(0xff10 + i) for i in range(10)]  # ０..９; CP932 0x824F..0x8258
SCALE = 4        # texels per screen unit for the English glyphs
SS = 4           # extra supersampling on top of SCALE when rasterizing
GAP = 2          # empty texels around each HD glyph so bilinear sampling never reaches a neighbour
# Extra alpha levels (PS2: 128 = opaque) written into free palette entries; the stock fonts use 0/32/64/96/128.
EXTRA_ALPHAS = [4, 8, 16, 24, 40, 48, 56, 75, 85, 107, 117]

# Per-font design (in screen units): source face size, weight, baseline row, tracking, space advance, squeeze.
PROFILES = {
    22: {'size': 17.5, 'weight': 340, 'baseline': 18, 'tracking': 0.35, 'space': 4.5, 'squeeze': 0.94},  # menus f010
    18: {'size': 14.6, 'weight': 380, 'baseline': 15, 'tracking': 0.3, 'space': 3.8, 'squeeze': 0.94},   # dialogue 50070
    17: {'size': 13.8, 'weight': 380, 'baseline': 14, 'tracking': 0.3, 'space': 3.6, 'squeeze': 0.94},   # f005 names
    13: {'size': 10.8, 'weight': 420, 'baseline': 11, 'tracking': 0.4, 'space': 3.0, 'squeeze': 0.94},   # HUD 50071
}


def _face(px, weight):
    face = ImageFont.truetype(str(NOTO), int(round(px)))
    try:
        axes = face.get_variation_axes()
        face.set_variation_by_axes([weight if b'eight' in a.get('name', b'') else a['default'] for a in axes])
    except (OSError, AttributeError):
        pass
    return face


def rasterize(cell, profile, scale=SCALE):
    """Return {char: (coverage image 'L' of (width*scale, cell*scale), width, advance, bearing)} in units."""
    hi = SS * scale                       # render pixels per screen unit
    face = _face(profile['size'] * hi, profile['weight'])
    ascent, _ = face.getmetrics()
    squeeze = profile.get('squeeze', 1.0)
    out = {}
    for ch in ASCII:
        if ch == ' ':
            out[ch] = (Image.new('L', (scale, cell * scale), 0), 1, int(round(profile['space'])), 0)
            continue
        advance = max(1, int(round(face.getlength(ch) * squeeze / hi + profile['tracking'])))
        pad = 3 * hi
        canvas = Image.new('L', (int(face.getlength(ch)) + 2 * pad, cell * hi + 2 * pad), 0)
        ImageDraw.Draw(canvas).text((pad, pad + profile['baseline'] * hi - ascent), ch, font=face, fill=255)
        if squeeze != 1.0:
            canvas = canvas.resize((max(1, int(round(canvas.width * squeeze))), canvas.height), Image.LANCZOS)
        origin = int(round(pad * squeeze))
        bbox = canvas.getbbox()
        require(bbox is not None, 'Empty glyph %r' % ch)
        # Ink left of the pen origin (j) gets a negative bearing: the renderer adds the signed bearing (lh at
        # EE 0x1c8bd8), so nothing is clipped.
        bearing = min(0, int(math.floor((bbox[0] - origin) / hi)))
        width = max(1, int(math.ceil((bbox[2] - origin) / hi)) - bearing)
        left = origin + bearing * hi
        sample = canvas.crop((left, pad, left + width * hi, pad + cell * hi))
        out[ch] = (sample.resize((width * scale, cell * scale), Image.BOX), width, advance, bearing)
    return out


def extend_palette(font):
    """Keep the stock CLUT entries and fill the free ones (all-zero and unused) with intermediate alpha levels
    of the same colour; return {alpha: index} for every usable entry."""
    used = set(font.pixels)
    entries = [bytes(font.clut[i * 4:i * 4 + 4]) for i in range(16)]
    stock = {i: e for i, e in enumerate(entries) if i in used or any(e)}
    rgb = next(e[:3] for e in stock.values() if e[3])
    require(all(e[:3] == rgb for e in stock.values() if e[3]), 'Stock palette mixes colours')
    levels = {e[3]: i for i, e in sorted(stock.items(), reverse=True)}
    extra = [a for a in EXTRA_ALPHAS if a not in levels]
    clut = bytearray(font.clut)
    for i in range(16):
        if i not in stock and extra:
            a = extra.pop(0)
            clut[i * 4:i * 4 + 4] = rgb + bytes([a])
            levels[a] = i
    font.clut = bytes(clut)
    return levels


def quantize(coverage, levels):
    """Coverage 0..255 -> palette index of the nearest alpha level (alpha = coverage^0.85 * 128)."""
    alphas = sorted(levels)
    table = []
    for c in range(256):
        a = 128 * (c / 255.0) ** 0.85
        table.append(levels[min(alphas, key=lambda x: abs(x - a))])
    return coverage.point(table)


def reclaim(font, keep_chars, start=0):
    """Repack the atlas with only the stock glyphs for ``keep_chars``; every other code is remembered and later
    pointed at '?' (by add_english). Used for fonts whose Japanese text is entirely translated (f005 names, the
    HUD lock-on/speaker font), so their atlases have room for English. Returns the first free row."""
    keep = sorted({font.map[Font.code(c)] for c in keep_chars if Font.code(c) in font.map})
    images = {}
    for g in keep:
        u0, v0, u1, v1 = font.glyphs[g]['uv']
        x0, y0, x1, y1 = (int(round(u0 * font.tw)), int(round(v0 * font.th)), int(round(u1 * font.tw)), int(round(v1 * font.th)))
        images[g] = (x1 - x0, y1 - y0, [bytes(font.pixels[(y0 + yy) * font.tw + x0:(y0 + yy) * font.tw + x1]) for yy in range(y1 - y0)])
    font.pixels = bytearray(len(font.pixels))
    x, y, row_h = GAP, start + GAP, 0
    for g in keep:
        w, h, rows = images[g]
        if x + w + GAP > font.tw:
            x, y, row_h = GAP, y + row_h + GAP, 0
        for yy, r in enumerate(rows):
            font.pixels[(y + yy) * font.tw + x:(y + yy) * font.tw + x + w] = r
        font.glyphs[g]['uv'] = (x / font.tw, y / font.th, (x + w) / font.tw, (y + h) / font.th)
        font.glyphs[g]['raw'] = None
        x += w + GAP
        row_h = max(row_h, h)
    keep_set = set(keep)
    font.dropped = [c for c, g in font.map.items() if g not in keep_set]
    return y + row_h


def fits(font, profile, scale, start=None):
    """True if the glyph set at ``scale`` packs into the free atlas rows (dry run on a copy of the pixels)."""
    glyphs = rasterize(font.cell, profile, scale)
    h = font.cell * scale
    x, y = GAP, (start if start is not None else font.used_rows()) + GAP
    for ch in ASCII:
        w = glyphs[ch][0].width
        if x + w + GAP > font.tw:
            x, y = GAP, y + h + GAP
        if y + h + GAP > font.th:
            return False
        x += w + GAP
    return True


def best_scale(font, profile=None, start=None):
    """Highest texel density (4, 3, 2, 1) whose glyph set fits in the free rows."""
    profile = profile or PROFILES[font.cell]
    return next(s for s in (4, 3, 2, 1) if fits(font, profile, s, start))


def add_english(font, profile=None, scale=None, start=None):
    """Add the ASCII set to ``font`` in place at ``scale`` texels per unit (default: best that fits). ``start`` is
    the first free atlas row (after ``reclaim``); by default the row below the last stock glyph."""
    profile = profile or PROFILES[font.cell]
    scale = scale or best_scale(font, profile, start)
    cell = font.cell
    glyphs = rasterize(cell, profile, scale)
    levels = extend_palette(font)
    h = cell * scale
    top = (start if start is not None else font.used_rows()) + GAP
    x, y = GAP, top
    placed = {}
    for ch in ASCII:
        image, width, advance, bearing = glyphs[ch]
        w = image.width
        if x + w + GAP > font.tw:
            x, y = GAP, y + h + GAP
        require(y + h + GAP <= font.th, 'Atlas full: no room for %r' % ch)
        idx = quantize(image, levels).tobytes()
        for yy in range(h):
            base = (y + yy) * font.tw + x
            require(not any(font.pixels[base - GAP:base + w + GAP]), 'Atlas area not empty at %d,%d' % (x, y + yy))
            font.pixels[base:base + w] = idx[yy * w:(yy + 1) * w]
        font.glyphs.append({'uv': (x / font.tw, y / font.th, (x + w) / font.tw, (y + h) / font.th),
                            # The renderer moves the pen by the bearing too (EE 0x1c8c04), so the stored advance
                            # is the design advance minus the bearing.
                            'bearing': bearing, 'width': width, 'advance': advance - bearing, 'pad': 0, 'raw': None})
        placed[ch] = len(font.glyphs) - 1
        x += w + GAP
    for ch, g in placed.items():
        font.map[Font.code(ch)] = g
    for i, ch in enumerate(FULLWIDTH_DIGITS):
        font.map[Font.code(ch)] = placed[str(i)]
    for code in getattr(font, 'dropped', ()):
        if code not in font.map or font.map[code] not in placed.values():
            font.map[code] = placed['?']
    return {'cell': cell, 'scale': scale, 'glyphs_added': len(placed), 'atlas_rows': [top, y + h],
            'advances': {ch: font.advance(ch) for ch in placed}}


def _alpha_atlas(font):
    lut = [min(255, font.clut[i * 4 + 3] * 2) for i in range(16)]
    atlas = Image.new('L', (font.tw, font.th))
    atlas.putdata([lut[p] for p in font.pixels])
    return atlas


def render(font, lines, scale=2, colour=(235, 235, 235), bg=(18, 24, 40), width=None, native=False):
    """Draw text the way the game does: each glyph's UV rectangle stretched over (width x cell) units at
    pen + bearing, pen += bearing + advance. ``scale`` is output pixels per unit (4 = what a 4x-upscaling emulator shows).
    ``native=True`` renders at 1 pixel per unit with GS-style bilinear sampling (one bilinear tap per pixel),
    then enlarges with nearest neighbour for viewing."""
    atlas = _alpha_atlas(font)
    s = 1 if native else scale
    lh = font.cell
    w = (width or max(font.width(l) for l in lines) + 8)
    canvas = Image.new('L', (w * s, (lh * len(lines) + 8) * s), 0)
    for n, line in enumerate(lines):
        pen = 4
        for ch in line:
            g = font.glyph(ch)
            u0, v0, u1, v1 = g['uv']
            box = (u0 * font.tw, v0 * font.th, u1 * font.tw, v1 * font.th)
            region = atlas.crop(tuple(int(round(b)) for b in box))
            size = (max(1, g['width'] * s), lh * s)
            if native and region.width > size[0]:
                # One bilinear tap per pixel centre, like the GS sampling a 4x texture at native resolution.
                glyph = region.transform(size, Image.AFFINE, (region.width / size[0], 0, 0, 0,
                                                              region.height / size[1], 0), Image.BILINEAR)
            elif region.width > size[0]:
                glyph = region.resize(size, Image.LANCZOS)
            else:
                glyph = region.resize(size, Image.NEAREST)
            px, py = (pen + g['bearing']) * s, (4 + n * lh) * s
            under = canvas.crop((px, py, px + size[0], py + size[1]))
            canvas.paste(Image.composite(glyph, under, glyph), (px, py))
            pen += g['bearing'] + g['advance']
    out = Image.composite(Image.new('RGB', canvas.size, colour), Image.new('RGB', canvas.size, bg), canvas)
    if native:
        out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    return out


def main():
    from ace_formats import bnd_child, read_iso_file, unpack, SOURCE_ISO, bnd_entries
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preview', action='store_true')
    a = ap.parse_args()
    data = read_iso_file(SOURCE_ISO, '/DATA.BIN')
    entry = next(e for e in bnd_entries(data) if e['name'].endswith('MenuCampaign.csc'))
    bundle = unpack(data[entry['offset']:entry['offset'] + entry['size']])
    font = Font(bnd_child(bundle, 'f010.ccm'), bnd_child(bundle, 'f010.tm2'))
    stock = Font(bnd_child(bundle, 'f010.ccm'), bnd_child(bundle, 'f010.tm2'))
    report = add_english(font)
    print({k: v for k, v in report.items() if k != 'advances'})
    if a.preview:
        out = ROOT / 'work/ui/vwf'
        out.mkdir(parents=True, exist_ok=True)
        sample = ['The quick brown fox jumps over the lazy dog. 0123456789',
                  'THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG! (j/q/g/y)',
                  'An elite task force under direct UCE command, formed from',
                  'the best units and pilots of each member organization.',
                  '"Boson Jump" - Nergal Heavy Industries; Earth Federation?']
        render(font, sample, scale=4, width=460).save(out / 'f010_english_hd_4x.png')
        render(font, sample, scale=2, width=460, native=True).save(out / 'f010_english_native_1x.png')
        render(stock, ['ＵＣＥ（地球統一機構）ロンド・ベル', 'アナザーセンチュリーズエピソード'],
               scale=4, width=460).save(out / 'f010_stock_japanese_4x.png')
        atlas = _alpha_atlas(font)
        atlas.crop((0, report['atlas_rows'][0] - 30, font.tw, report['atlas_rows'][1] + 2)).save(out / 'f010_atlas_hd_rows.png')
        for old in ('f010_english_sample.png', 'f010_stock_japanese.png', 'f010_atlas_new_rows.png'):
            (out / old).unlink(missing_ok=True)
        print('previews in', out)


if __name__ == '__main__':
    main()
