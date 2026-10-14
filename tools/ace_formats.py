"""Readers and writers for Another Century's Episode (SLPS-25394) data formats.

All offsets were checked against the stock disc. Formats:

* DATA.BIN / menu bundles: ``BND\\0`` archive. Header: magic, ``ffff0000``, version ``0xd3``, total size,
  entry count, two flag words, then 16-byte entries ``id, offset, size, name_offset`` from byte 32.
* ``.csc``: LZSS-packed resource (same codec as ACE 3, see ``unpack``/``pack``).
* ``.fmg``: text table. ``00 00 01 00``, size, 0, range count, slot count, pointer table offset, 0; ranges of
  ``base, first_id, last_id``; then one u32 pointer per slot (0 = empty); CP932 strings.
* ``.ccm``: glyph map. ``00 00 01 00``, size, cell height, 0, u16 range count, u16 glyph count, range offset (32),
  glyph offset; ranges ``first_code, last_code, first_glyph``; 24-byte glyphs: four float UVs
  ``u0 v0 u1 v1`` and int16 ``bearing, width, advance, 0``. Codes are CP932 values (one or two bytes, big-endian).
* ``.tm2``: single GS texture. u32 total, pixel bytes, 1, transfer mode (0 = linear, 1 = PSMT4 data uploaded
  as PSMCT32 at half width / quarter height, i.e. GS-swizzled), u64 TEX0, 8 bytes, pixels, then CLUT.
"""
import binascii
import io
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_ISO = ROOT / "Another Century's Episode (Japan).iso"
SECTOR = 2048


def require(value, message):
    if not value:
        raise ValueError(message)


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def align(n, a=SECTOR):
    return (n + a - 1) // a * a


# ---------------------------------------------------------------- ISO9660 / UDF

def iso_files(stream):
    """Map '/PATH/NAME' -> {'offset', 'size'} for every file in the ISO9660 tree."""
    stream.seek(16 * SECTOR)
    pvd = stream.read(SECTOR)
    require(pvd[:7] == b'\x01CD001\x01', 'Expected ISO9660 primary volume')
    found = {}

    def walk(lba, size, parent):
        stream.seek(lba * SECTOR)
        data = stream.read(size)
        at = 0
        while at < len(data):
            length = data[at]
            if not length:
                at = (at // SECTOR + 1) * SECTOR
                continue
            record = data[at:at + length]
            at += length
            name = record[33:33 + record[32]]
            if name in (b'\0', b'\1'):
                continue
            name = parent + '/' + name.decode('ascii').split(';')[0]
            extent, fsize = u32(record, 2), u32(record, 10)
            if record[25] & 2:
                walk(extent, fsize, name)
            else:
                found[name] = {'offset': extent * SECTOR, 'size': fsize}
    walk(u32(pvd, 158), u32(pvd, 166), '')
    return found


def read_iso_file(path, name):
    with open(path, 'rb') as f:
        rec = iso_files(f)[name]
        f.seek(rec['offset'])
        return f.read(rec['size'])


def fix_udf_tag(raw):
    """Recompute a UDF descriptor tag's CRC and checksum in place."""
    length = struct.unpack_from('<H', raw, 10)[0]
    require(16 + length <= len(raw), 'UDF CRC length exceeds descriptor')
    struct.pack_into('<H', raw, 8, binascii.crc_hqx(bytes(raw[16:16 + length]), 0))
    raw[4] = 0
    raw[4] = sum(raw[:16]) & 255


# ---------------------------------------------------------------- BND

def bnd_entries(data):
    require(data[:4] == b'BND\0', 'Not a BND archive')
    count = u32(data, 16)
    out = []
    for i in range(count):
        ident, offset, size, name_at = struct.unpack_from('<4I', data, 32 + i * 16)
        name = data[name_at:data.index(b'\0', name_at)].decode('cp932') if name_at else str(ident)
        out.append({'index': i, 'id': ident, 'offset': offset, 'size': size, 'name': name})
    return out


def bnd_child(data, suffix):
    hits = [e for e in bnd_entries(data) if e['name'].lower().endswith(suffix.lower())]
    require(len(hits) == 1, 'Expected one BND child ending with %s, found %d' % (suffix, len(hits)))
    e = hits[0]
    return data[e['offset']:e['offset'] + e['size']]


def bnd_replace(data, replacements, alignment=SECTOR):
    """Rebuild a BND with some children replaced (by name suffix). Header and names are kept; children are
    re-laid in their original order on ``alignment`` boundaries, starting where the first child started."""
    entries = bnd_entries(data)
    start = min(e['offset'] for e in entries)
    require(all(e['offset'] % alignment == 0 for e in entries), 'Unexpected child alignment')
    order = sorted(entries, key=lambda e: e['offset'])
    used = set()
    out = bytearray(data[:start])
    for e in order:
        body = data[e['offset']:e['offset'] + e['size']]
        for suffix, new in replacements.items():
            if e['name'].lower().endswith(suffix.lower()):
                body = new
                used.add(suffix)
        out += bytes(align(len(out), alignment) - len(out))
        struct.pack_into('<II', out, 32 + e['index'] * 16 + 4, len(out), len(body))
        out += body
    require(used == set(replacements), 'Unmatched BND replacements: %s' % (set(replacements) - used))
    tail = align(len(out), alignment)
    out += bytes(tail - len(out))
    struct.pack_into('<I', out, 12, len(out))
    return bytes(out)


# ---------------------------------------------------------------- CSC (LZSS)

CSC_MAGIC = b'\x00\x01\x00\x00'
WINDOW, MAX_LEN = 4096, 16


def is_packed(data):
    return len(data) >= 12 and data[:4] == CSC_MAGIC and data[8:12] == b'\0\0\0\0'


def unpack(data):
    """Decode a .csc resource. While fewer than 4096 bytes are out a reference is an absolute output offset;
    afterwards the window base slides (copy starts at len(out) - 4096 + field)."""
    require(is_packed(data), 'Not a packed resource')
    size = struct.unpack('>I', data[4:8])[0]
    out = bytearray()
    at = 12
    while len(out) < size:
        flags = data[at]
        at += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags >> bit & 1:
                b0, b1 = data[at], data[at + 1]
                at += 2
                field = b0 << 4 | b1 >> 4
                source = field if len(out) < WINDOW else len(out) - WINDOW + field
                for k in range((b1 & 15) + 1):
                    out.append(out[source + k])
            else:
                out.append(data[at])
                at += 1
    return bytes(out)


def pack(plain, align_to=16, depth=128):
    """LZSS with hash chains and one-step lazy matching; output decodes with ``unpack`` and the game's
    decoder (references of 3..16 bytes, never a zero length nibble)."""
    out = bytearray(CSC_MAGIC + struct.pack('>I', len(plain)) + b'\0\0\0\0')
    chains, n, at = {}, len(plain), 0
    flag_at, bit, items = None, 8, bytearray()

    def insert(p):
        if p + 3 <= n:
            chains.setdefault(plain[p:p + 3], []).append(p)

    def longest(pos):
        best_len, best_src = 0, 0
        if pos + 3 <= n:
            candidates = chains.get(plain[pos:pos + 3], ())
            limit = min(MAX_LEN, n - pos)
            for p in reversed(candidates[-depth:]):
                if pos - p > WINDOW:
                    break
                k = 3
                while k < limit and plain[p + k] == plain[pos + k]:
                    k += 1
                if k > best_len:
                    best_len, best_src = k, p
                    if k == limit:
                        break
        return best_len, best_src

    while at < n:
        best_len, best_src = longest(at)
        if 3 <= best_len < MAX_LEN and at + 1 < n:
            # Lazy matching: prefer a literal now if the next position starts a longer match.
            insert(at)
            nxt_len, _ = longest(at + 1)
            chains[plain[at:at + 3]].pop() if at + 3 <= n else None
            if nxt_len > best_len:
                best_len = 0
        if bit == 8:
            out += items
            items = bytearray()
            flag_at = len(out)
            out.append(0)
            bit = 0
        if best_len >= 3:
            field = best_src if at < WINDOW else WINDOW - (at - best_src)
            require(0 <= field < WINDOW, 'Reference out of window')
            out[flag_at] |= 1 << bit
            items += bytes([field >> 4, (field & 15) << 4 | (best_len - 1)])
            for p in range(at, at + best_len):
                insert(p)
            at += best_len
        else:
            items.append(plain[at])
            insert(at)
            at += 1
        bit += 1
    out += items
    out += bytes(-len(out) % align_to)
    return bytes(out)


# ---------------------------------------------------------------- FMG text tables

def fmg_read(data):
    require(data[:4] == b'\0\0\1\0', 'Not an FMG table')
    size, zero, groups, count, table, reserved = struct.unpack_from('<6I', data, 4)
    require(table == 28 + 12 * groups and table + count * 4 <= size <= len(data), 'Malformed FMG header')
    ids = []
    for g in range(groups):
        base, first, last = struct.unpack_from('<3I', data, 28 + 12 * g)
        require(base == len(ids) and first <= last, 'Malformed FMG range')
        ids.extend(range(first, last + 1))
    require(len(ids) == count, 'FMG slot count mismatch')
    rows = {}
    for i, ident in enumerate(ids):
        p = u32(data, table + 4 * i)
        if p:
            end = data.index(b'\0', p, size)
            rows[ident] = data[p:end].decode('cp932')
        else:
            rows[ident] = None
    return rows


def fmg_build(rows, pad_to=16):
    """Build an FMG from {id: text or None}. Consecutive ids share a range; None keeps an empty slot."""
    ids = sorted(rows)
    ranges = []
    for i in ids:
        if ranges and i == ranges[-1][2] + 1:
            ranges[-1][2] = i
        else:
            ranges.append([None, i, i])
    base = 0
    for r in ranges:
        r[0] = base
        base += r[2] - r[1] + 1
    table = 28 + 12 * len(ranges)
    pool_at = table + 4 * len(ids)
    pool = bytearray()
    pointers = []
    for i in ids:
        text = rows[i]
        if text is None:
            pointers.append(0)
            continue
        pointers.append(pool_at + len(pool))
        pool += text.encode('cp932') + b'\0'
    size = pool_at + len(pool)
    size += -size % pad_to
    out = bytearray(b'\0\0\1\0' + struct.pack('<6I', size, 0, len(ranges), len(ids), table, 0))
    for r in ranges:
        out += struct.pack('<3I', *r)
    out += b''.join(struct.pack('<I', p) for p in pointers)
    out += pool
    out += bytes(size - len(out))
    require(fmg_read(bytes(out)) == rows, 'FMG round trip failed')
    return bytes(out)


# ---------------------------------------------------------------- GS swizzle (PSMT4 uploaded as PSMCT32)

def _address4(x, y, width):
    """Byte-nibble address of PSMT4 texel (x, y) in GS memory (PCSX2 GSTables layout, as used by ACE 3)."""
    import numpy as np
    page = y // 128 * (width // 128) + x // 128
    bx, by = x // 32 % 4, y // 16 % 8
    block = (bx & 1) * 2 + (bx & 2) * 4 + (by & 1) + (by & 2) * 2 + (by & 4) * 4
    column = ((x & 1) << 3) | ((x & 2) << 4) | ((((x >> 2) ^ (y >> 1) ^ (y >> 2)) & 1) << 6)
    column = column | ((x & 24) >> 2) | ((y & 1) << 4) | ((y & 2) >> 1) | ((y & 4) << 5) | ((y & 8) << 5)
    return page * 16384 + block * 512 + column


def _address32(x, y, width):
    page = y // 32 * (width // 64) + x // 64
    bx, by = x // 8 % 8, y // 8 % 4
    block = (bx & 1) + (bx & 2) * 2 + (bx & 4) * 4 + (by & 1) * 2 + (by & 2) * 4
    column = (x & 1) + (x & 6) * 2 + (y & 1) * 2 + (y & 6) * 8
    return (page * 2048 + block * 64 + column) * 4


def _swizzle_maps(width, height):
    import numpy as np
    tw = width // 2
    ty, tx = np.mgrid[0:height // 4, 0:tw]
    src32 = _address32(tx, ty, tw).ravel()            # vram byte address of each transferred 32-bit word
    y, x = np.mgrid[0:height, 0:width]
    a4 = _address4(x, y, width).ravel()                # vram nibble address of each texel
    return src32, a4


def swizzled_to_pixels(raw, width, height):
    import numpy as np
    src32, a4 = _swizzle_maps(width, height)
    words = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 4)
    vram = np.zeros(len(raw), dtype=np.uint8)
    for k in range(4):
        vram[src32 + k] = words[:, k]
    return bytearray(((vram[a4 // 2] >> ((a4 & 1) * 4)) & 15).astype(np.uint8).tobytes())


def pixels_to_swizzled(pixels, width, height):
    import numpy as np
    src32, a4 = _swizzle_maps(width, height)
    vram = np.zeros(width * height // 2, dtype=np.uint8)
    px = np.frombuffer(bytes(pixels), dtype=np.uint8)
    lo = (a4 & 1) == 0
    np.bitwise_or.at(vram, a4[lo] // 2, px[lo])
    np.bitwise_or.at(vram, a4[~lo] // 2, (px[~lo] << 4).astype(np.uint8))
    out = np.zeros((len(src32), 4), dtype=np.uint8)
    for k in range(4):
        out[:, k] = vram[src32 + k]
    return out.tobytes()


# ---------------------------------------------------------------- CCM glyph maps

class Font:
    """A CCM glyph map with its TM2 atlas (PSMT4, linear transfer)."""

    def __init__(self, ccm, tm2):
        require(ccm[:4] == b'\0\0\1\0', 'Not a CCM font')
        self.header = bytearray(ccm[:32])
        self.cell = ccm[8]
        nr, ng, ro, go = struct.unpack_from('<HHII', ccm, 16)
        require(ro == 32 and go == 32 + nr * 12, 'Unexpected CCM layout')
        self.map = {}
        for i in range(nr):
            first, last, index = struct.unpack_from('<III', ccm, ro + i * 12)
            for code in range(first, last + 1):
                self.map[code] = index + code - first
        self.glyphs = []
        for g in range(ng):
            uv = struct.unpack_from('<4f', ccm, go + g * 24)
            metrics = struct.unpack_from('<4h', ccm, go + g * 24 + 16)
            raw = ccm[go + g * 24:go + g * 24 + 24]
            self.glyphs.append({'uv': uv, 'bearing': metrics[0], 'width': metrics[1],
                                'advance': metrics[2], 'pad': metrics[3], 'raw': raw})
        total, length, count, mode = struct.unpack_from('<4I', tm2, 0)
        require(total == len(tm2) and count == 1 and mode in (0, 1), 'Expected one TM2 texture')
        self.mode = mode
        self.tex_header = tm2[:32]
        tex0 = struct.unpack_from('<Q', tm2, 16)[0]
        self.psm = (tex0 >> 20) & 63
        # PSMT4HH (44) uploaded linearly stores two palette indices per byte exactly like PSMT4 (as in ACE 3's
        # HUD font patch); the original GPU header is kept by tm2_bytes.
        require(self.psm == 20 or (self.psm == 44 and mode == 0), 'Only PSMT4 / linear PSMT4HH atlases are supported')
        self.tw, self.th = 1 << ((tex0 >> 26) & 15), 1 << ((tex0 >> 30) & 15)
        require(length == self.tw * self.th // 2, 'Atlas size mismatch')
        raw = tm2[32:32 + length]
        if mode == 0:
            self.pixels = bytearray(v for b in raw for v in (b & 15, b >> 4))
        else:
            self.pixels = swizzled_to_pixels(raw, self.tw, self.th)
        self.clut = tm2[32 + length:]

    @staticmethod
    def code(char):
        return int.from_bytes(char.encode('cp932'), 'big')

    def glyph(self, char):
        g = self.map.get(self.code(char))
        return None if g is None else self.glyphs[g]

    def advance(self, char):
        """Pen movement for ``char``: the renderer adds the bearing to the pen before drawing (EE 0x1c8c04) and
        the advance after it (0x1c8ce8)."""
        g = self.glyph(char)
        require(g is not None, 'No glyph for %r' % char)
        return g['bearing'] + g['advance']

    def width(self, text):
        return sum(self.advance(c) for c in text)

    def ccm_bytes(self):
        ranges = []
        for code, index in sorted(self.map.items()):
            if ranges and code == ranges[-1][1] + 1 and index == ranges[-1][2] + code - ranges[-1][0]:
                ranges[-1][1] = code
            else:
                ranges.append([code, code, index])
        out = bytearray(self.header)
        for r in ranges:
            out += struct.pack('<III', *r)
        glyph_at = len(out)
        for g in self.glyphs:
            if g.get('raw') is not None:
                out += g['raw']
            else:
                out += struct.pack('<4f4h', *g['uv'], g['bearing'], g['width'], g['advance'], 0)
        out += bytes(-len(out) % 16)
        struct.pack_into('<I', out, 4, len(out))
        struct.pack_into('<HHII', out, 16, len(ranges), len(self.glyphs), 32, glyph_at)
        return bytes(out)

    def tm2_bytes(self):
        if self.mode == 0:
            raw = bytes(self.pixels[i] | self.pixels[i + 1] << 4 for i in range(0, len(self.pixels), 2))
        else:
            raw = pixels_to_swizzled(self.pixels, self.tw, self.th)
        return bytes(self.tex_header) + raw + bytes(self.clut)

    def used_rows(self):
        """Lowest atlas row not covered by any glyph rectangle."""
        return max(int(round(g['uv'][3] * self.th)) for g in self.glyphs)
