"""Check the game's HUD font upload instructions against its texture storage.

The small interpreter executes only the integer setup up to sceGsSetDefLoadImage.
It does not run the game or claim to verify subsequent rendering/VRAM lifetime.
"""
import struct

from ace_formats import require, u32

LINEAR_UPLOAD = 0x17c530
SWIZZLED_UPLOAD = 0x17d1d0
HUD_UPLOAD_CALLS = (0x1e165c, 0x1e17ec)


def file_offset(address):
    return address - 0x100000 + 0x80


def jal(address):
    return 0x0c000000 | (address >> 2)


def first_transfer(elf, texture, entry):
    """Trace actual EE instructions through their first GS transfer setup call."""
    memory = bytearray(0x2000000)
    memory[0x100000:0x100000 + len(elf) - 0x80] = elf[0x80:]
    memory[0x400000:0x400000 + len(texture)] = texture
    r = [0] * 32
    r[4], r[29] = 0x400000, 0x1fff000
    pc, pending, trace = entry, None, []
    mask = (1 << 64) - 1

    def signed(value, bits):
        value &= (1 << bits) - 1
        return value - (1 << bits) if value & (1 << (bits - 1)) else value

    for _ in range(256):
        if pc == 0x101488:
            return dict(entry=hex(entry), base=r[5], buffer_width=r[6], psm=r[7],
                        x=r[8], y=r[9], width=r[10], height=r[11], instructions=len(trace))
        word = int.from_bytes(memory[pc:pc + 4], 'little')
        trace.append(pc)
        op, rs, rt, rd, shift, fn = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31, (word >> 6) & 31, word & 63
        immediate = signed(word & 0xffff, 16)
        address = (r[rs] + immediate) & 0xffffffff
        previous_pending, pending = pending, None
        if op in (9, 25):  # addiu/daddiu
            r[rt] = r[rs] + immediate
        elif op == 15:
            r[rt] = signed((word & 0xffff) << 16, 32)
        elif op == 12:
            r[rt] = r[rs] & (word & 0xffff)
        elif op == 13:
            r[rt] = r[rs] | (word & 0xffff)
        elif op == 11:
            r[rt] = int(r[rs] < (immediate & mask))
        elif op in (4, 5):
            take = (r[rs] == r[rt]) if op == 4 else (r[rs] != r[rt])
            pending = pc + 4 + immediate * 4 if take else pc + 8
        elif op == 3:
            r[31] = pc + 8
            pending = (pc & 0xf0000000) | ((word & 0x3ffffff) << 2)
        elif op in (0x24, 0x25, 0x37):  # lbu/lhu/ld
            size = {0x24: 1, 0x25: 2, 0x37: 8}[op]
            r[rt] = int.from_bytes(memory[address:address + size], 'little')
        elif op in (0x3f, 0x1f):  # sd/sq (saved upper halves unused before first call)
            size = 8 if op == 0x3f else 16
            memory[address:address + size] = r[rt].to_bytes(size, 'little')
        elif op == 0:
            if fn == 0:
                r[rd] = signed(r[rt] << shift, 32)
            elif fn == 2:
                r[rd] = signed((r[rt] & 0xffffffff) >> shift, 32)
            elif fn == 4:
                r[rd] = signed(r[rt] << (r[rs] & 31), 32)
            elif fn in (0x21, 0x2d):
                r[rd] = r[rs] + r[rt]
            elif fn == 0x18:  # EE MULT rd, rs, rt also writes low product to rd
                r[rd] = signed(signed(r[rs], 32) * signed(r[rt], 32), 32)
            elif fn == 0x2b:
                r[rd] = int(r[rs] < r[rt])
            elif fn in (0x38, 0x3c):
                r[rd] = r[rt] << (shift + (32 if fn == 0x3c else 0))
            elif fn in (0x3a, 0x3e):
                r[rd] = r[rt] >> (shift + (32 if fn == 0x3e else 0))
            elif fn == 0x3f:
                r[rd] = signed(r[rt], 64) >> (shift + 32)
            else:
                raise ValueError('Unsupported instruction at %#x: %#x' % (pc, word))
        else:
            raise ValueError('Unsupported instruction at %#x: %#x' % (pc, word))
        r = [value & mask for value in r]
        r[0] = 0
        pc = previous_pending if previous_pending is not None else pc + 4
    raise ValueError('Transfer setup did not terminate')


def check_calls(elf, texture):
    require(u32(texture, 12) == 1, 'Expected swizzled font storage')
    tex0 = struct.unpack_from('<Q', texture, 16)[0]
    width, height = 1 << ((tex0 >> 26) & 15), 1 << ((tex0 >> 30) & 15)
    require((width, height, (tex0 >> 20) & 63) == (1024, 512, 20), 'Unexpected shared atlas')
    # Resource initialization replaces TBP0 before either mission startup path.
    texture = bytearray(texture)
    base = u32(elf, file_offset(0x2a64d8))
    require(base == 0x2600, 'Shared HUD texture base differs')
    struct.pack_into('<Q', texture, 16, (tex0 & ~0x3fff) | base)
    results = []
    for site in HUD_UPLOAD_CALLS:
        word = u32(elf, file_offset(site))
        require(word >> 26 == 3, 'HUD upload site is no longer a JAL')
        entry = (word & 0x3ffffff) << 2
        transfer = first_transfer(elf, texture, entry)
        require(transfer['base'] == base, 'Upload destination differs')
        require((transfer['psm'], transfer['width'], transfer['height'], transfer['buffer_width']) ==
                (0, width // 2, height // 4, width // 128),
                'HUD uploader interprets swizzled font as linear texels at %#x: %r' % (site, transfer))
        results.append(dict(call_site=hex(site), **transfer))
    return results
