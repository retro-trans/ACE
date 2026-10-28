"""Compile story captions into a runtime overlay for the decoded RGB32 frames.

The PSS files stay original. The hook runs before the decoded picture enters
the display queue, so captions travel with pictures even when playback stalls.
No gameplay font, GS allocation or extra DMA packet is needed.
"""
import argparse
import hashlib
import json
import struct

import numpy as np
import movie_text as mt
from ace_formats import ROOT, require, u32

BASE = 0x34a480  # original end of BSS; reserve the payload before every heap
OPEN = 0x2001a0
QUEUE = 0x1f24c0
STATE = BASE + 0x800
DIRECTORY = STATE + 16
DATA = BASE + 0x1000
W, H = 512, 448
OUT = ROOT / 'work/output/movie-overlay'


def off(va):
    return va - 0x100000 + 0x80


class Asm:
    """Small explicit MIPS assembler: no toolchain or implicit delay slots."""
    def __init__(self, base):
        self.base, self.words, self.labels, self.fixups = base, [], {}, []

    def emit(self, word):
        self.words.append(word)

    def label(self, name):
        self.labels[name] = self.base + len(self.words) * 4

    def i(self, op, rt, rs, value):
        self.emit(op << 26 | rs << 21 | rt << 16 | (value & 65535))

    def r(self, fn, rd, rs=0, rt=0, shift=0):
        self.emit(rs << 21 | rt << 16 | rd << 11 | shift << 6 | fn)

    def li(self, reg, value):
        self.i(15, reg, 0, value >> 16)
        self.i(13, reg, reg, value)

    def branch(self, op, rs, rt, label):
        self.fixups.append((len(self.words), label))
        self.i(op, rt, rs, 0)
        self.emit(0)

    def jump(self, addr):
        self.emit(2 << 26 | (addr >> 2))
        self.emit(0)

    def finish(self):
        for index, label in self.fixups:
            delta = (self.labels[label] - (self.base + index * 4 + 4)) // 4
            require(-32768 <= delta < 32768, 'Overlay branch out of range')
            self.words[index] |= delta & 65535
        return struct.pack('<%dI' % len(self.words), *self.words)


def code():
    # Registers: v0=2 v1=3 a0..a3=4..7 t0..t7=8..15 t8=24 t9=25.
    a = Asm(BASE)
    a.label('open')
    a.li(8, STATE)
    a.i(43, 0, 8, 0)                 # disable for MOVIE0 / unknown movies
    a.i(43, 0, 8, 4)                 # decoded picture number, reset on open
    a.i(9, 9, 0, 1)
    a.branch(5, 4, 9, 'open_done')
    a.i(9, 9, 5, -1)
    a.i(11, 9, 9, 22)
    a.branch(4, 9, 0, 'open_done')
    a.r(0, 9, rt=5, shift=2)
    a.li(10, DIRECTORY)
    a.r(33, 10, 10, 9)
    a.i(35, 9, 10, 0)
    a.i(43, 9, 8, 0)
    a.label('open_done')
    a.i(9, 29, 29, -0x110)          # displaced original prologue
    a.r(45, 6, 4, 0)                # daddu a2,a0,zero (original word)
    a.jump(OPEN + 8)

    a.label('queue')
    a.li(8, STATE)
    a.i(35, 9, 8, 0)                # selected movie descriptor table
    a.branch(4, 9, 0, 'publish')
    a.i(35, 10, 8, 4)
    a.i(9, 11, 10, 1)
    a.i(43, 11, 8, 4)
    # Only the verified 512x448, two-picture RGB32 ring is supported.
    for delta, expected in ((0x24, W), (0x28, H), (0x10, W * H), (12, 2)):
        a.i(35, 11, 4, delta)
        a.li(12, expected)
        a.branch(5, 11, 12, 'publish')
    a.i(35, 11, 9, 0)               # card count
    a.i(9, 9, 9, 4)
    a.label('find')
    a.branch(4, 11, 0, 'publish')
    a.i(35, 12, 9, 0)               # inclusive first picture
    a.r(43, 13, 10, 12)
    a.branch(5, 13, 0, 'publish')
    a.i(35, 13, 9, 4)               # exclusive end picture
    a.r(43, 14, 10, 13)
    a.branch(5, 14, 0, 'draw')
    a.i(9, 11, 11, -1)
    a.i(9, 9, 9, 24)
    a.branch(4, 0, 0, 'find')
    a.label('draw')
    a.r(35, 10, 10, 12)
    a.r(0, 10, rt=10, shift=1)
    a.i(35, 12, 9, 16)              # uint16 opacity [0,256] per picture
    a.r(33, 12, 12, 10)
    a.i(37, 15, 12, 0)
    a.i(35, 8, 9, 8)                # packed pixel stream
    a.i(35, 9, 9, 12)               # stream byte count
    a.r(33, 9, 9, 8)
    a.i(35, 10, 4, 4)               # producer index (0 or 1)
    a.i(11, 11, 10, 2)
    a.branch(4, 11, 0, 'publish')
    a.li(11, W * H * 4)
    a.r(25, 0, 10, 11)
    a.r(18, 10)
    a.i(35, 11, 4, 0)               # uncached ring buffer address
    a.r(33, 10, 10, 11)
    a.li(5, 0x3ffff)
    a.i(9, 6, 0, 255)
    a.li(25, 0x80000000)            # GS opaque alpha
    a.label('chunk')
    a.branch(4, 8, 9, 'publish')
    a.i(35, 11, 8, 0)
    a.r(36, 12, 11, 5)              # 18-bit destination pixel offset
    a.r(0, 12, rt=12, shift=2)
    a.r(33, 12, 12, 10)
    a.i(9, 8, 8, 4)
    a.r(2, 24, rt=11, shift=18)      # encoded chunk length
    a.r(33, 24, 24, 8)
    a.label('value')
    a.branch(4, 8, 24, 'next_chunk')
    a.i(36, 14, 8, 0)               # literal gray, or FF count gray
    a.i(9, 8, 8, 1)
    a.i(9, 13, 0, 1)
    a.branch(5, 14, 6, 'paint')
    a.i(36, 13, 8, 0)
    a.i(36, 14, 8, 1)
    a.i(9, 8, 8, 2)
    a.label('paint')
    a.r(25, 0, 14, 15)
    a.r(18, 14)
    a.r(2, 14, rt=14, shift=8)
    a.r(0, 11, rt=14, shift=8)
    a.r(37, 14, 14, 11)
    a.r(0, 11, rt=14, shift=16)
    a.r(37, 14, 14, 11)
    # The shift also made an alpha byte; explicitly keep only RGB.
    a.r(0, 14, rt=14, shift=8)
    a.r(2, 14, rt=14, shift=8)
    a.r(37, 14, 14, 25)
    a.label('pixels')
    a.i(43, 14, 12, 0)
    a.i(9, 13, 13, -1)
    a.i(9, 12, 12, 4)
    a.branch(5, 13, 0, 'pixels')
    a.branch(4, 0, 0, 'value')
    a.label('next_chunk')
    a.i(9, 8, 8, 3)
    a.i(9, 11, 0, -4)
    a.r(36, 8, 8, 11)
    a.branch(4, 0, 0, 'chunk')
    a.label('publish')
    a.emit(0x0000040f)              # sync.l before queue publication/DMA
    a.jump(0x1f2e10)                # original publication function, same a0/ra
    raw = a.finish()
    require(len(raw) <= STATE - BASE, 'Overlay code exceeds reserved region')
    return raw, a.labels


def tiled(a):
    """IPU RGB32 order, verified against the supplied ending RAM snapshot."""
    return a.reshape(H // 16, 16, W // 16, 16).transpose(2, 0, 1, 3).reshape(-1)


def untiled(a):
    return a.reshape(W // 16, H // 16, 16, 16).transpose(1, 2, 0, 3).reshape(H, W)


def spans(values, mask):
    # Aligned chunks: offset:18 + encoded byte length:14; literal gray bytes
    # with FF,count,gray for repetitions. Text tops out below FF, so no escape
    # ambiguity. This keeps antialiasing lossless without a large font atlas.
    v, m = tiled(values), tiled(mask)
    require(int(v.max()) < 255, 'Pixel FF is reserved for run encoding')
    changes = np.flatnonzero(np.r_[False, m, False][1:] != np.r_[False, m, False][:-1])
    out = bytearray()
    for first, last in zip(changes[::2], changes[1::2]):
        # Cap literal block length to fit the 14-bit encoded length field.
        for start in range(int(first), int(last), 8192):
            end = min(start + 8192, int(last))
            pixels = v[start:end]
            edges = np.flatnonzero(np.r_[True, pixels[1:] != pixels[:-1], True])
            enc = bytearray()
            for lo, hi in zip(edges[:-1], edges[1:]):
                n, value = int(hi - lo), int(pixels[lo])
                while n:
                    k = min(n, 255)
                    enc.extend((255, k, value) if k >= 4 else [value] * k)
                    n -= k
            out.extend(struct.pack('<I', start | len(enc) << 18))
            out.extend(enc)
            out.extend(bytes(-len(out) % 4))
    return bytes(out)


def compile_payload():
    raw, labels = code()
    payload = bytearray(raw)
    payload += bytes(DATA - BASE - len(payload))
    summary = {'format': 1, 'method': 'decoded-picture-overlay', 'base': hex(BASE),
               'hooks': {k: hex(v) for k, v in labels.items() if k in ('open', 'queue')}, 'movies': []}

    def append(data, alignment=4):
        payload.extend(bytes(-len(payload) % alignment))
        address = BASE + len(payload)
        payload.extend(data)
        return address

    for movie_id in range(1, 23):
        name = 'M1_MOVIE%03d' % movie_id
        path = mt.SPEC / (name + '.en.json')
        doc = json.loads(path.read_text(encoding='utf-8'))
        es, _ = mt.elementary(name)
        segments = doc['segments']
        table = append(bytes(4 + 24 * len(segments)))
        struct.pack_into('<I', payload, DIRECTORY - BASE + movie_id * 4, table)
        struct.pack_into('<I', payload, table - BASE, len(segments))
        rows = []
        last_end = 0
        for index, (k, spec) in enumerate(sorted(enumerate(segments), key=lambda item: item[1]['frames'][0])):
            require(spec['type'] == 'static' and spec['refs'] == ['black'], 'Nonblack story card')
            a, b = spec['frames']
            require(last_end <= a < b, 'Overlapping or empty overlay cards')
            require(all(line.get('en') for line in spec['lines']), 'Missing English caption')
            last_end = b
            card = mt.StaticCard(name, es, k, spec)
            # Fully erase original strokes and their faint MPEG fringes; preserve
            # the moving picture outside the lettering rows. Text is antialiased
            # from the same 4x font rendering as the current translated movies.
            mask = mt.dilate(card.ink, 4) | (card.text > 0)
            gray = np.rint(card.text * (spec['colour'][0] - 16) * 255 / 219).clip(0, 255).astype(np.uint8)
            runs = spans(gray, mask)
            fades = np.rint(np.clip(card.energy / card.peak, 0, 1) * 256).astype('<u2').tobytes()
            require(len(fades) == (b - a) * 2, 'Fade table length differs')
            rp, fp = append(runs), append(fades)
            struct.pack_into('<6I', payload, table - BASE + 4 + index * 24,
                             a, b, rp, len(runs), fp, spec['card'])
            rows.append({'card': spec['card'], 'frames': [a, b], 'pixel_stream_bytes': len(runs),
                         'pixels': int(mask.sum()), 'lines': [line['en'] for line in spec['lines']]})
        summary['movies'].append({'movie': name, 'source_spec_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                  'cards': rows})
        print(name, len(rows), 'cards; payload', len(payload), 'bytes', flush=True)
    payload.extend(bytes(-len(payload) % 128))
    summary.update(payload_bytes=len(payload), heap_start=hex(BASE + len(payload)),
                   sha256=hashlib.sha256(payload).hexdigest(), card_count=sum(len(m['cards']) for m in summary['movies']))
    require(summary['card_count'] == 171, 'Story caption coverage changed')
    require(len(payload) <= 2 * 1024 * 1024, 'Overlay reservation exceeds 2 MiB budget')
    return bytes(payload), summary


def patch_elf(elf, report):
    payload, summary = compile_payload()
    out = bytearray(elf)
    phoff = u32(out, 28)
    require(struct.unpack_from('<HH', out, 42) == (32, 2), 'Unexpected ELF program headers')
    require(struct.unpack_from('<8I', out, phoff + 32) == (1, 1872896, BASE, BASE, 0, 0, 6, 16),
            'Expected original empty second load segment')
    checks = {OPEN: 0x27bdfef0, OPEN + 4: 0x0080302d,
              QUEUE: 0x0c07cb84, QUEUE + 4: 0x0200202d,
              0x1001d0: 0x3c040035, 0x1001d8: 0x2484a480,
              0x12bee4: 0x3c040035, 0x12bef0: 0x2484a480,
              0x12bf54: 0x3c060035, 0x12bf60: 0x24c6a480,
              0x2a12d4: BASE}
    for address, expected in checks.items():
        require(u32(out, off(address)) == expected, 'Overlay input mismatch at %#x' % address)
    _, labels = code()
    struct.pack_into('<2I', out, off(OPEN), 0x08000000 | labels['open'] >> 2, 0)
    struct.pack_into('<I', out, off(QUEUE), 0x0c000000 | labels['queue'] >> 2)
    new_end = BASE + len(payload)
    # BSS clearing still stops at BASE; payload data must survive startup.
    for hi, lo, reg in ((0x1001d0, 0x1001d8, 4), (0x12bee4, 0x12bef0, 4), (0x12bf54, 0x12bf60, 6)):
        struct.pack_into('<I', out, off(hi), 0x3c000000 | reg << 16 | ((new_end + 0x8000) >> 16))
        struct.pack_into('<I', out, off(lo), 0x24000000 | reg << 21 | reg << 16 | (new_end & 65535))
    struct.pack_into('<I', out, off(0x2a12d4), new_end)  # libc sbrk cursor
    out.extend(bytes(-len(out) % 128))
    at = len(out)
    out.extend(payload)
    struct.pack_into('<8I', out, phoff + 32, 1, at, BASE, BASE, len(payload), len(payload), 7, 128)
    summary['elf_payload_offset'] = at
    summary['heap_references'] = [hex(a) for a in (0x1001d0, 0x12bee4, 0x12bf54, 0x2a12d4)]
    report['movie_overlay'] = summary
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'payload.bin').write_bytes(payload)
    (OUT / 'manifest.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return bytes(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--compile', action='store_true')
    args = ap.parse_args()
    if args.compile:
        payload, report = compile_payload()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'payload.bin').write_bytes(payload)
        (OUT / 'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('Compiled', report['card_count'], 'cards:', len(payload), 'bytes')
