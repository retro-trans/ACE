"""Trace the actual 1P/2P frame-refresh gates with supplied dialogue state.

External status queries and transfers are stubbed; this checks control flow,
not gameplay. Upload descriptors are separately traced from the actual ELF.
"""
import itertools
import struct

from ace_formats import require, u32
from font_upload import file_offset, first_transfer, SWIZZLED_UPLOAD


def frame_trace(elf, mode, dialogue, flag, resource=True):
    start, end = (0x1e1ab0, 0x1e1ae0) if mode == '1P' else (0x1e1b50, 0x1e1b78)
    r = [0] * 32
    r[17] = 0x500000
    pointer = 0x400000 if resource else 0
    pc, pending, calls = start, None, []
    for _ in range(64):
        if pc == end:
            return calls
        require(start <= pc < end, 'Frame trace escaped expected routine')
        word = u32(elf, file_offset(pc))
        op, rs, rt, rd = word >> 26, word >> 21 & 31, word >> 16 & 31, word >> 11 & 31
        imm = struct.unpack('<h', struct.pack('<H', word & 65535))[0]
        delayed, pending = pending, None
        if word == 0:
            pass
        elif op == 9:
            r[rt] = r[rs] + imm
        elif op == 0 and word & 63 == 0x2d:
            r[rd] = r[rs] + r[rt]
        elif op == 0 and word & 63 == 0x21:
            r[rd] = r[rs] + r[rt]
        elif op == 0x23:
            require(r[rs] + imm == 0x5000c0, 'Unexpected frame memory read')
            r[rt] = pointer
        elif op in (4, 5):
            take = (r[rs] == r[rt]) if op == 4 else (r[rs] != r[rt])
            pending = ('branch', pc + 4 + imm * 4 if take else pc + 8)
        elif op == 3:
            r[31] = pc + 8
            pending = ('call', (word & 0x3ffffff) << 2)
        else:
            raise ValueError('Unsupported frame instruction at %#x: %#x' % (pc, word))
        r[0] = 0
        pc += 4
        if delayed:
            kind, target = delayed
            if kind == 'branch':
                pc = target
            else:
                if target == 0x236a50:
                    require(r[4] == 0x10, 'Unexpected status flag query')
                    r[2] = int(flag)
                elif target == 0x1aca20:
                    r[2] = int(dialogue)
                elif target == 0x1c9ca0:
                    require(r[4] == 0, 'Expected shared dialogue resource')
                    r[2] = pointer
                elif target in (0x17d030, SWIZZLED_UPLOAD):
                    # 17d030 preserves its original null-texture guard.
                    if r[4]:
                        calls.append(dict(target=hex(target), resource=r[4],
                                          descriptor=r[5] if target == 0x17d030 else None))
                else:
                    raise ValueError('Unexpected frame callee %#x' % target)
                pc = r[31]
    raise ValueError('Frame trace did not terminate')


def check_refresh(elf, texture):
    results = []
    for mode, dialogue, flag, present in itertools.product(('1P', '2P'), (False, True), (False, True), (False, True)):
        calls = frame_trace(elf, mode, dialogue, flag, present)
        require(len(calls) == int(present),
                'Shared font missing from %s frame (dialogue=%s, flag=%s)' % (mode, dialogue, flag))
        results.append(dict(mode=mode, dialogue=dialogue, flag=flag, resource_present=present, uploads=calls))
    texture = bytearray(texture)
    tex0 = struct.unpack_from('<Q', texture, 16)[0]
    struct.pack_into('<Q', texture, 16, (tex0 & ~0x3fff) | 0x2600)
    descriptors = [
        first_transfer(elf, texture, 0x17d4d0, {4: 0x500000, 5: 0x500060, 6: 0x400000}),
        first_transfer(elf, texture, SWIZZLED_UPLOAD),
    ]
    for descriptor in descriptors:
        require(tuple(descriptor[k] for k in ('base', 'psm', 'width', 'height', 'buffer_width')) ==
                (0x2600, 0, 512, 128, 8), 'Incorrect frame refresh descriptor')
    return dict(scenarios=results, transfer_descriptors=descriptors, runtime_verified=False)
