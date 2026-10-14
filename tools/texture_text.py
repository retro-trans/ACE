"""Replace Japanese lettering baked into UI textures.

    python tools/texture_text.py detect <name> ...   # annotated proofs with numbered label boxes (work/ui/texture_text/)
    python tools/texture_text.py render <name> ...   # before/after proofs from the label specs
Spec files: work/translation/en/textures/<name>.json
  {"name", "labels": [{"box": [x0, y0, x1, y1], "ja", "en", "align": "center|left|right",
                       "vertical": false, "grow": [left, right], "color": [r, g, b] (optional)}]}
"box" is the Japanese lettering's extent (from detect, adjusted by hand where needed). The lettering is erased by
interpolating each row (or column, for vertical labels) between the background just outside the box, then the
English is drawn in Noto Sans JP (OFL) in the lettering's own colour, shrunk/condensed to fit the box widened by
"grow" pixels, and the image is mapped back onto the texture's own palette, so size, format and palette stay as
they were. Vertical labels are drawn rotated, reading top to bottom, or bottom to top with "upward": true (for lettering stored rotated counter-clockwise).
"""
import json
import struct
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ace_formats import ROOT, require, u32
from texture_audit import decode, textures

SPEC = ROOT / 'work/translation/en/textures'
PROOF = ROOT / 'work/ui/texture_text'
NOTO = Path(r'C:\Windows\Fonts\NotoSansJP-VF.ttf')
WINDOW_BND = '\\window\\bnd\\'


def by_name():
    """Texture name -> (key, {'data', 'where'}). Menu textures are named by file (t0403.tm2); textures inside
    the window bundles by bundle and child id (InGameWindow.bnd#8402)."""
    out = {}
    for key, t in textures().items():
        leaf = t['where'][0].split('\\')[-1]
        out.setdefault(leaf, (key, t))
    from dialogue_source import open_data, unnamed_bnd
    f, db = open_data()
    for e in db.entries:
        if WINDOW_BND in e['name'].lower():
            data = db.read(e)
            for ident, (o, n) in unnamed_bnd(data).items():
                d = data[o:o + n]
                if len(d) >= 64 and u32(d, 8) == 1 and 64 <= u32(d, 0) <= n:
                    name = '%s#%d' % (e['name'].split('\\')[-1], ident)
                    out.setdefault(name, (name, {'data': d[:u32(d, 0)], 'where': [e['name'] + '#%d' % ident]}))
    f.close()
    return out


def text_mask(im):
    w, h = im.size
    px = im.load()
    mask = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 60 and min(r, g, b) > 150 and max(r, g, b) - min(r, g, b) < 70:
                mask[y][x] = True
    return mask


def components(mask, gap=2):
    h, w = len(mask), len(mask[0])
    seen = [[False] * w for _ in range(h)]
    boxes = []
    for y in range(h):
        for x in range(w):
            if mask[y][x] and not seen[y][x]:
                stack = [(x, y)]
                seen[y][x] = True
                x0 = x1 = x
                y0 = y1 = y
                n = 0
                while stack:
                    cx, cy = stack.pop()
                    n += 1
                    x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
                    for dy in range(-gap, gap + 1):
                        for dx in range(-gap - 1, gap + 2):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not seen[ny][nx]:
                                seen[ny][nx] = True
                                stack.append((nx, ny))
                if n >= 6 and (x1 - x0 >= 3 or y1 - y0 >= 3):
                    boxes.append([x0, y0, x1 + 1, y1 + 1])
    return boxes


def merge_lines(boxes, gap=9):
    """Join character boxes that share a text line (vertical overlap > half) and are close horizontally;
    pad by 2 px for the drop shadow."""
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                ov = min(a[3], b[3]) - max(a[1], b[1])
                if ov > 0.5 * min(a[3] - a[1], b[3] - b[1]) and (max(a[0], b[0]) - min(a[2], b[2])) <= gap:
                    boxes[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del boxes[j]
                    changed = True
                    break
            if changed:
                break
    return [[b[0] - 1, b[1] - 1, b[2] + 2, b[3] + 2] for b in boxes]


def detect(name, table):
    key, t = table[name]
    im = decode(t['data'])
    boxes = merge_lines(components(text_mask(im)))
    PROOF.mkdir(parents=True, exist_ok=True)
    s = 3
    big = Image.new('RGB', (im.width * s, im.height * s), (60, 60, 80))
    big.paste(im.resize((im.width * s, im.height * s), Image.NEAREST), (0, 0), im.resize((im.width * s, im.height * s), Image.NEAREST))
    d = ImageDraw.Draw(big)
    for i, b in enumerate(boxes):
        d.rectangle([b[0] * s, b[1] * s, b[2] * s - 1, b[3] * s - 1], outline=(255, 0, 0))
        d.text((b[0] * s + 1, b[1] * s - 10), str(i), fill=(255, 255, 0))
    big.save(PROOF / ('%s_detect.png' % name.replace('.', '_')))
    (PROOF / ('%s_boxes.json' % name.replace('.', '_'))).write_text(json.dumps(boxes), encoding='utf-8')
    return boxes


def _bg_fill(im, box, vertical):
    """Erase a box by linear interpolation between the pixels just outside it (rows, or columns if vertical)."""
    px = im.load()
    x0, y0, x1, y1 = box
    w, h = im.size
    if not vertical:
        for y in range(y0, y1):
            left = px[max(0, x0 - 1), y]
            right = px[min(w - 1, x1), y]
            for x in range(x0, x1):
                t = (x - x0 + 0.5) / max(1, x1 - x0)
                px[x, y] = tuple(int(round(left[k] + (right[k] - left[k]) * t)) for k in range(4))
    else:
        for x in range(x0, x1):
            top = px[x, max(0, y0 - 1)]
            bottom = px[x, min(h - 1, y1)]
            for y in range(y0, y1):
                t = (y - y0 + 0.5) / max(1, y1 - y0)
                px[x, y] = tuple(int(round(top[k] + (bottom[k] - top[k]) * t)) for k in range(4))


def _text_image(text, height, max_width, colour, weight=560, cap=0.6):
    """Render ``text`` on a fixed baseline band ``height`` px tall (cap height = ``cap`` x height, so every label
    of the same box height gets the same letter size); condense horizontally to 70 percent, then shrink."""
    band = height
    scale = 1.0
    while True:
        cap_px = band * cap * scale * 4
        size = cap_px / 0.733                      # Noto Sans cap height is 0.733 em
        face = ImageFont.truetype(str(NOTO), max(8, int(round(size))))
        try:
            face.set_variation_by_axes([weight])
        except (OSError, AttributeError):
            pass
        ascent, descent = face.getmetrics()
        width4 = face.getlength(text)
        img = Image.new('L', (int(width4) + 16, ascent + descent + 8), 0)
        ImageDraw.Draw(img).text((8, 4), text, font=face, fill=255)
        ink = img.getbbox() or (0, 0, 1, 1)
        baseline = 4 + ascent
        top = int(baseline - cap_px - (band * 4 - cap_px) * 0.5)   # even split: room for g/j/p/q/y descenders
        img = img.crop((ink[0], top, ink[2], top + band * 4))
        w = img.width / 4
        if w <= max_width:
            out_w = max(1, int(round(w)))
            break
        if w * 0.7 <= max_width:
            out_w = max(1, int(max_width))
            break
        scale *= 0.92
    small = img.resize((out_w, band), Image.LANCZOS)
    rgba = Image.new('RGBA', small.size, tuple(colour) + (0,))
    rgba.putalpha(small)
    return rgba


def _shadowed(im, text, x, y):
    """Composite ``text`` with a 1 px dark drop shadow, like the stock lettering."""
    shadow = Image.new('RGBA', text.size, (0, 0, 0, 0))
    shadow.putalpha(text.getchannel('A').point(lambda a: a * 3 // 4))
    im.alpha_composite(shadow, (min(im.width - text.width, x + 1), min(im.height - text.height, y + 1)))
    im.alpha_composite(text, (x, y))


def lettering_colour(im, box):
    px = im.load()
    best = None
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            p = px[x, y]
            if p[3] > 60 and (best is None or sum(p[:3]) > sum(best[:3])):
                best = p
    return list(best[:3]) if best else [235, 235, 235]


def render_label(im, lab):
    x0, y0, x1, y1 = lab['box']
    vertical = lab.get('vertical', False)
    colour = lab.get('color') or lettering_colour(im, lab['box'])
    _bg_fill(im, [x0, y0, x1, y1], vertical)
    gl, gr = lab.get('grow', [0, 0])
    if not vertical:
        avail = (x1 - x0) + gl + gr
        text = _text_image(lab['en'], lab.get('height', y1 - y0), avail, colour)
        if gl or gr:
            _bg_fill(im, [x0 - gl, y0, x1 + gr, y1], False)
        align = lab.get('align', 'center')
        left = x0 - gl
        if align == 'center':
            left = x0 - gl + (avail - text.width) // 2
        elif align == 'right':
            left = x1 + gr - text.width
        top = y0 + ((y1 - y0) - text.height + 1) // 2
        _shadowed(im, text, max(0, left), max(0, top))
    else:
        avail = (y1 - y0) + gl + gr
        text = _text_image(lab['en'], lab.get('height', x1 - x0), avail, colour).rotate(90 if lab.get('upward') else -90, expand=True)
        if gl or gr:
            _bg_fill(im, [x0, y0 - gl, x1, y1 + gr], True)
        top = y0 - gl + (avail - text.height) // 2
        left = x0 + ((x1 - x0) - text.width + 1) // 2
        _shadowed(im, text, max(0, left), max(0, top))


def palette_of(data):
    tex0 = struct.unpack_from('<Q', data, 16)[0]
    psm = (tex0 >> 20) & 63
    length = u32(data, 4)
    clut = data[32 + length:]
    n = 16 if psm == 20 else 256
    pal = [tuple(clut[i * 4:i * 4 + 4]) for i in range(n)]
    if psm == 19:  # CSM1 order: logical index -> stored entry
        order = [(i & ~0x18) | ((i & 0x08) << 1) | ((i & 0x10) >> 1) for i in range(256)]
    else:
        order = list(range(16))
    return psm, length, pal, order


def encode(data, im):
    """Map an RGBA image back onto the texture's palette and return new texture bytes (same size)."""
    psm, length, pal, order = palette_of(data)
    logical = [pal[order[i]] for i in range(len(order))]
    def premul(r, g, b, a):
        # Compare colours premultiplied by alpha, so faint edge pixels of the lettering map to faint palette
        # entries instead of snapping to visible grey on transparent backgrounds.
        return (r * a / 255.0, g * a / 255.0, b * a / 255.0, a)
    cand = [(i, premul(p[0], p[1], p[2], min(255, p[3] * 2))) for i, p in enumerate(logical)]
    cache = {}
    idx = []
    for p in im.getdata():
        if p not in cache:
            q = premul(*p)
            cache[p] = min(cand, key=lambda c: (c[1][0] - q[0]) ** 2 + (c[1][1] - q[1]) ** 2 + (c[1][2] - q[2]) ** 2 + 2 * (c[1][3] - q[3]) ** 2)[0]
        idx.append(cache[p])
    if psm == 20:
        raw = bytes(idx[i] | idx[i + 1] << 4 for i in range(0, len(idx), 2))
    else:
        raw = bytes(idx)
    require(len(raw) == length, 'Encoded size differs')
    return data[:32] + raw + data[32 + length:]


def apply_spec(data, spec):
    im = decode(data).copy()
    for lab in spec['labels']:
        if lab.get('en'):
            render_label(im, lab)
    return encode(data, im), im


def main():
    cmd, names = sys.argv[1], sys.argv[2:]
    table = by_name()
    PROOF.mkdir(parents=True, exist_ok=True)
    for name in names:
        if cmd == 'detect':
            print(name, len(detect(name, table)), 'boxes')
        elif cmd == 'render':
            key, t = table[name]
            spec = json.loads((SPEC / ('%s.json' % name.replace('.', '_'))).read_text(encoding='utf-8'))
            new, im = apply_spec(t['data'], spec)
            before = decode(t['data'])
            after = decode(new)
            s = 2
            sheet = Image.new('RGB', (before.width * s * 2 + 8, before.height * s), (60, 60, 80))
            for n, img in enumerate((before, after)):
                big = img.resize((img.width * s, img.height * s), Image.NEAREST)
                sheet.paste(big, (n * (before.width * s + 8), 0), big)
            sheet.save(PROOF / ('%s_render.png' % name.replace('.', '_')))
            print(name, 'rendered')


if __name__ == '__main__':
    main()
