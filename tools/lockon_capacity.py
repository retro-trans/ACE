"""Keep lock-on rendering and GIF allocation at the same capacity.

Stock code limits target names to 12 glyphs (the longest Japanese label).
English labels have up to 24 ASCII bytes and still obey the 156-unit UI limit.
Only the two target-widget capacity arguments change; font size stays at 12.
"""
import struct
from ace_formats import require, u32
from font_upload import file_offset, jal
from dialogue_buffer import allocation

CAPACITY = 24
SITES = {
    0x1d7228: (0x2404000c, 0x1d722c, 0x1c9220, 'allocation'),
    0x1d86dc: (0x240a000c, 0x1d86d8, 0x1c8a10, 'drawing'),
}


def patch(elf, report):
    for address, (original, call, target, _) in SITES.items():
        require(u32(elf, file_offset(address)) == original,
                'Unexpected lock-on capacity instruction at %#x' % address)
        require(u32(elf, file_offset(call)) == jal(target),
                'Unexpected lock-on call at %#x' % call)
        struct.pack_into('<I', elf, file_offset(address), (original & 0xffff0000) | CAPACITY)
    report['lockon_capacity'] = verify(elf)


def verify(elf):
    require(u32(elf, file_offset(0x1d8620)) == 0x2404000c,
            'Lock-on font size must stay at 12')
    for address, (original, call, target, _) in SITES.items():
        require(u32(elf, file_offset(address)) == (original & 0xffff0000) | CAPACITY,
                'Lock-on capacity mismatch at %#x' % address)
        require(u32(elf, file_offset(call)) == jal(target), 'Lock-on call changed')
    return dict(glyphs_before=12, glyphs_after=CAPACITY,
                bytes_before=allocation(elf, 12), bytes_after=allocation(elf, CAPACITY),
                sites={role:hex(address) for address, (_, _, _, role) in SITES.items()})
