"""Reclaim Japanese glyphs, preserving English screen metrics and required symbols."""
import struct

from ace_formats import Font, require
from vwf_font import add_english, reclaim


def character(code):
    try:
        return code.to_bytes(1 if code < 256 else 2, 'big').decode('cp932')
    except (UnicodeError, OverflowError):
        return ''


def japanese(c):
    return bool(c) and ('\u3040' <= c <= '\u30ff' or '\u3400' <= c <= '\u9fff'
                       or '\uff61' <= c <= '\uff9f' or '\uf900' <= c <= '\ufaff')


def symbols(font):
    return {character(c) for c in font.map if character(c) and c > 126
            and not japanese(character(c))}


def compact(font):
    font.map = {c: g for c, g in font.map.items() if not japanese(character(c))}
    used = sorted(set(font.map.values()))
    indices = {g: i for i, g in enumerate(used)}
    font.glyphs = [font.glyphs[g] for g in used]
    font.map = {c: indices[g] for c, g in font.map.items()}


def metrics(previous, current):
    for c in range(32, 127):
        for field in ('bearing', 'width', 'advance', 'pad'):
            current.glyph(chr(c))[field] = previous.glyph(chr(c))[field]


def resize(font, width, height, header=None):
    """Change atlas dimensions without moving its existing pixels."""
    require(width >= font.tw or not any(font.pixels), 'Cannot crop occupied columns')
    old_w, old_h = font.tw, font.th
    pixels = bytearray(width * height)
    for y in range(min(old_h, height)):
        pixels[y * width:y * width + min(old_w, width)] = font.pixels[y * old_w:y * old_w + min(old_w, width)]
    for g in font.glyphs:
        a, b, c, d = g['uv']
        g['uv'] = a * old_w / width, b * old_h / height, c * old_w / width, d * old_h / height
        g['raw'] = None
    font.tw, font.th, font.pixels = width, height, pixels
    h = bytearray(header or font.tex_header)
    length = width * height // 2
    struct.pack_into('<II', h, 0, 32 + length + len(font.clut), length)
    tex0 = struct.unpack_from('<Q', h, 16)[0]
    mask = (63 << 14) | (15 << 26) | (15 << 30)
    tex0 = ((tex0 & ~mask) | (width // 64 << 14)
            | ((width.bit_length() - 1) << 26) | ((height.bit_length() - 1) << 30))
    struct.pack_into('<Q', h, 16, tex0)
    font.tex_header = bytes(h)


def rebuild(ccm, tm2):
    previous = Font(ccm, tm2)
    add_english(previous)
    result = Font(ccm, tm2)
    start = reclaim(result, symbols(result))
    add_english(result, scale=4, start=start)
    metrics(previous, result)
    compact(result)
    height = 1 << (result.used_rows() - 1).bit_length()
    if height < result.th:
        resize(result, result.tw, height)
    return result.ccm_bytes(), result.tm2_bytes()


def shared(dialogue_ccm, dialogue_tm2, hud_ccm, hud_tm2, hud_keep):
    """Two 4x fonts in the existing 1024x512 dialogue allocation, with separate CLUTs."""
    d = Font(dialogue_ccm, dialogue_tm2)
    h = Font(hud_ccm, hud_tm2)
    require((d.tw, d.th, d.psm, d.mode) == (1024, 512, 20, 1), 'Unexpected dialogue atlas')
    require((h.tw, h.th, h.psm, h.mode) == (256, 128, 44, 0), 'Unexpected HUD atlas')
    old_d = Font(dialogue_ccm, dialogue_tm2)
    old_h = Font(hud_ccm, hud_tm2)
    add_english(old_d)
    add_english(old_h, start=reclaim(old_h, hud_keep))
    start = reclaim(d, symbols(d))
    dr = add_english(d, scale=4, start=start)
    metrics(old_d, d)
    resize(h, d.tw, d.th, d.tex_header)
    h.mode, h.psm = d.mode, d.psm
    start = reclaim(h, symbols(h) | hud_keep, start=dr['atlas_rows'][1])
    hr = add_english(h, scale=4, start=start)
    metrics(old_h, h)
    require(not any(a and b for a, b in zip(d.pixels, h.pixels)), 'Shared glyphs overlap')
    pixels = bytearray(a or b for a, b in zip(d.pixels, h.pixels))
    d.pixels = pixels
    h.pixels = bytearray(pixels)
    compact(d)
    compact(h)
    return (d.ccm_bytes(), d.tm2_bytes(), h.ccm_bytes(), h.tm2_bytes()), {
        'atlas': [1024, 512], 'format': 'PSMT4', 'texels_per_unit': 4,
        'dialogue_rows': dr['atlas_rows'], 'hud_rows': hr['atlas_rows'],
        'shared_gpu_bytes': 262144, 'separate_palettes': True,
        'japanese_glyphs': 0, 'runtime_verified': False}
