"""4x HUD lettering in a larger linear PSMT4HH atlas; screen metrics stay unchanged.

The expanded GPU allocation needs gameplay verification. No executable/font-slot changes.
"""
import struct

from ace_formats import Font, require
from vwf_font import add_english, reclaim


def rebuild(ccm, tm2, keep):
    old = Font(ccm, tm2)
    start = reclaim(old, keep)
    add_english(old, start=start)
    new = Font(ccm, tm2)
    require((new.tw, new.th, new.psm, new.mode) == (256, 128, 44, 0), 'Unexpected HUD atlas')
    # Keep every original rectangle in pixel coordinates before reclaiming its live glyphs.
    for g in new.glyphs:
        u0, v0, u1, v1 = g['uv']
        g['uv'] = (u0 / 2, v0 / 4, u1 / 2, v1 / 4)
        g['raw'] = None
    pixels = bytearray(512 * 512)
    for y in range(128):
        pixels[y * 512:y * 512 + 256] = new.pixels[y * 256:(y + 1) * 256]
    new.tw, new.th, new.pixels = 512, 512, pixels
    header = bytearray(new.tex_header)
    length = 512 * 512 // 2
    struct.pack_into('<II', header, 0, 32 + length + len(new.clut), length)
    tex0 = struct.unpack_from('<Q', header, 16)[0]
    mask = (63 << 14) | (15 << 26) | (15 << 30)
    tex0 = (tex0 & ~mask) | (8 << 14) | (9 << 26) | (9 << 30)
    struct.pack_into('<Q', header, 16, tex0)
    new.tex_header = bytes(header)
    start = reclaim(new, keep)
    result = add_english(new, scale=4, start=start)
    # Supersampling may round a bearing/width differently; preserve the shipped layout exactly.
    for c in range(32, 127):
        a, b = old.glyph(chr(c)), new.glyph(chr(c))
        for field in ('bearing', 'width', 'advance', 'pad'):
            b[field] = a[field]
    result.update(atlas=[new.tw, new.th], previous_atlas=[256, 128],
                  gpu_format='PSMT4HH', metrics_preserved=True, runtime_verified=False)
    return new.ccm_bytes(), new.tm2_bytes(), result
