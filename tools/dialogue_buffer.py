"""Size the operator's GIF drawing buffer for the translated message budget.

This is separate from the 132-byte typewriter buffer. The original reserves
50 glyphs at 0x2018dc but draws the full typed length without that limit.
"""
import struct

from ace_formats import require, u32
from font_upload import file_offset, jal

CAPACITY_ADDRESS = 0x2018dc
CAPACITY = 128
ORIGINAL_INSTRUCTION = 0x24040032  # addiu a0, zero, 50
PATCHED_INSTRUCTION = 0x24040000 | CAPACITY


def allocation(elf, count):
    """Execute the actual nonzero-count sizing arithmetic at EE 0x1c9230."""
    expected = (0x000410c0, 0x24030008, 0x00441023,
                0x00621821, 0x24620003, 0x00021100)
    at = file_offset(0x1c9230)
    require(struct.unpack_from('<6I', elf, at) == expected,
            'Dialogue packet size routine changed')
    # sll v0,a0,3; li v1,8; subu v0,v0,a0; addu v1,v1,v0;
    # addiu v0,v1,3; sll v0,v0,4. Zero is handled by the preceding branch.
    return ((8 + (count << 3) - count + 3) << 4) if count else 0


def patch(elf, report):
    at = file_offset(CAPACITY_ADDRESS)
    require(u32(elf, at) == ORIGINAL_INSTRUCTION, 'Unexpected dialogue capacity instruction')
    require(u32(elf, at + 4) == jal(0x1c9220), 'Unexpected dialogue allocator call')
    before, after = allocation(elf, 50), allocation(elf, CAPACITY)
    struct.pack_into('<I', elf, at, PATCHED_INSTRUCTION)
    report['operator_drawing_buffer'] = dict(address=hex(CAPACITY_ADDRESS),
        glyphs_before=50, glyphs_after=CAPACITY, bytes_before=before,
        bytes_after=after, extra_bytes_per_widget=after-before)


def verify(elf):
    require(u32(elf, file_offset(CAPACITY_ADDRESS)) == PATCHED_INSTRUCTION,
            'Operator drawing buffer still uses the original 50-glyph capacity')
    require(u32(elf, file_offset(CAPACITY_ADDRESS) + 4) == jal(0x1c9220),
            'Unexpected dialogue allocator call')
    return dict(glyph_capacity=CAPACITY, allocated_bytes=allocation(elf, CAPACITY),
                reported_53_glyph_bytes=allocation(elf, 53),
                original_overflow_bytes=allocation(elf, 53)-allocation(elf, 50),
                runtime_verified=False)
