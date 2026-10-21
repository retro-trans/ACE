"""Version and Retro Trans credit in the title screen's lower-right corner."""
import re
import struct
import math

from PIL import Image, ImageDraw, ImageFont
from ace_formats import require
from texture_text import NOTO, encode

TEXTURE = 't3105.tm2'
LAYOUT = 'l014.mnl'
GROUP = 'github.com / retro-trans'
# l014's copyright sprite maps atlas (0,440) to screen (32,364), without scaling.
# The widened sprite reaches screen x=512; ink stops at x=500 (12px safe margin).
RIGHT = 468
ROWS = (482, 498)
SIZE = 9


def stamp_texture(original, translated, version):
    require(re.fullmatch(r'0\.\d+\.\d+(?:-[A-Za-z0-9_-]+)?', version) is not None,
            'Invalid title build version')
    im = translated.copy()
    scale = 4
    font = ImageFont.truetype(str(NOTO), SIZE * scale)
    axes = font.get_variation_axes()
    font.set_variation_by_axes([600 if b'eight' in a.get('name', b'') else a['default'] for a in axes])
    bounds = []
    for text, top in zip(('v' + version, GROUP), ROWS):
        box = font.getbbox(text, stroke_width=scale)
        tile = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]))
        ImageDraw.Draw(tile).text((-box[0], -box[1]), text, font=font, fill=(235, 235, 235, 255),
                                 stroke_width=scale, stroke_fill=(0, 0, 0, 255))
        tile = tile.resize((min(98, math.ceil(tile.width / scale)), math.ceil(tile.height / scale)), Image.LANCZOS)
        x = RIGHT - tile.width
        actual = (x, top, RIGHT, top + tile.height)
        require(actual[0] >= (370 if top == ROWS[0] else 300) and actual[3] <= 512,
                'Title stamp does not fit its clear atlas area')
        require(im.crop(actual).getchannel('A').getbbox() is None, 'Title stamp overlaps existing artwork')
        im.alpha_composite(tile, (x, top))
        bounds.append(list(actual))
    return encode(original, im), dict(version=version, group=GROUP,
                                     atlas_bounds=bounds,
                                     screen_bounds=[[x0 + 32, y0 - 76, x1 + 32, y1 - 76]
                                                    for x0, y0, x1, y1 in bounds])


def patch_layout(data):
    require(len(data) == 0x4a0, 'Unexpected title layout size')
    sprite = struct.unpack_from('<12i', data, 0x48)
    require(sprite == (3105, 0, -224, -36, 224, 36, 256, 400, 0, 440, 448, 512),
            'Title copyright sprite differs')
    out = bytearray(data)
    struct.pack_into('<i', out, 0x58, 256)  # Screen right = 256 + 256.
    struct.pack_into('<i', out, 0x70, 480)  # Preserve 1:1 mapping of the existing pixels.
    return bytes(out)


def preview(texture, layout):
    """Reconstruct the static title sprites in screen coordinates, not an emulator capture."""
    from texture_audit import decode
    atlas = decode(texture)
    canvas = Image.new('RGBA', (512, 448), (20, 30, 40, 255))
    for index in (0, 1, 4):  # logo, copyright/stamp, Press START
        _, _, left, top, right, bottom, x, y, u0, v0, u1, v1 = struct.unpack_from('<12i', layout, 16 + 56 * index)
        tile = atlas.crop((u0, v0, u1, v1)).resize((right - left, bottom - top), Image.LANCZOS)
        canvas.alpha_composite(tile, (x + left, y + top))
    return canvas
