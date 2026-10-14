"""Decode every distinct TM2 texture on the disc and lay them out on contact sheets for a visual text audit.

    python tools/texture_audit.py     # writes work/ui/textures/sheet_NN.png and textures.json (key -> locations)

Formats on this disc are all linear (transfer mode 0): PSMT8 (19) with a 256-entry CLUT (CSM1 block order) and
PSMT4 (20) with a 16-entry CLUT. PS2 alpha 0x80 is opaque.
"""
import hashlib
import json
import struct
from PIL import Image, ImageDraw
from ace_formats import ROOT, bnd_entries, u32, unpack

OUT = ROOT / 'work/ui/textures'


def decode(d):
    tex0 = struct.unpack_from('<Q', d, 16)[0]
    psm = (tex0 >> 20) & 63
    w, h = 1 << ((tex0 >> 26) & 15), 1 << ((tex0 >> 30) & 15)
    length = u32(d, 4)
    raw = d[32:32 + length]
    clut = d[32 + length:]
    if psm == 20:
        idx = [v for b in raw for v in (b & 15, b >> 4)]
        pal = [tuple(clut[i * 4:i * 4 + 4]) for i in range(16)]
    elif psm == 19:
        idx = list(raw)
        pal = [tuple(clut[i * 4:i * 4 + 4]) for i in range(256)]
        # CSM1: within each 32-entry block, entries 8-15 and 16-23 are swapped.
        pal = [pal[(i & ~0x18) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)] for i in range(256)]
    else:
        return None
    w = min(w, length * (2 if psm == 20 else 1) // h) if h else w
    im = Image.new('RGBA', (w, h))
    im.putdata([(p[0], p[1], p[2], min(255, p[3] * 2)) for p in (pal[i] for i in idx[:w * h])])
    return im


def textures():
    from dialogue_source import open_data
    f, db = open_data()
    found = {}
    for e in db.entries:
        n = e['name']
        blobs = []
        if n.lower().endswith('.tm2'):
            blobs.append((n, db.read(e)))
        elif n.lower().endswith('.csc') and '\\menu\\' in n.lower():
            b = unpack(db.read(e))
            blobs += [(n + ':' + c['name'], b[c['offset']:c['offset'] + c['size']]) for c in bnd_entries(b)
                      if c['name'].lower().endswith('.tm2')]
        for where, d in blobs:
            if len(d) >= 32 and u32(d, 0) == len(d) and u32(d, 8) == 1:
                key = hashlib.sha1(d).hexdigest()[:10]
                found.setdefault(key, {'data': d, 'where': []})['where'].append(where)
    f.close()
    return found


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    found = textures()
    keys = sorted(found, key=lambda k: found[k]['where'][0])
    index = {}
    cell, per = 260, 20
    for s in range(0, len(keys), per):
        sheet = Image.new('RGB', (cell * 5, (cell + 14) * 4), (40, 40, 60))
        draw = ImageDraw.Draw(sheet)
        for n, k in enumerate(keys[s:s + per]):
            im = decode(found[k]['data'])
            label = '%d %s' % (s + n, found[k]['where'][0].split('\\')[-1])
            index[s + n] = {'key': k, 'where': found[k]['where'], 'size': im.size if im else None}
            if im:
                im.save(OUT / ('%03d_%s.png' % (s + n, k)))
                th = im.copy()
                th.thumbnail((cell - 4, cell - 4))
                bg = Image.new('RGB', th.size, (90, 90, 110))
                bg.paste(th, (0, 0), th)
                sheet.paste(bg, ((n % 5) * cell + 2, (n // 5) * (cell + 14) + 14))
            draw.text(((n % 5) * cell + 2, (n // 5) * (cell + 14)), label, fill=(255, 255, 0))
        sheet.save(OUT / ('sheet_%02d.png' % (s // per)))
    (OUT / 'textures.json').write_text(json.dumps(index, indent=1), encoding='utf-8')
    print(len(keys), 'textures,', (len(keys) + per - 1) // per, 'sheets ->', OUT)


if __name__ == '__main__':
    main()
