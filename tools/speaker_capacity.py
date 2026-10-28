"""Raise the radio-name draw count while retaining its existing 50-glyph buffer."""
import struct
from ace_formats import require, u32
from font_upload import file_offset, jal

ADDRESS = 0x201af0
ORIGINAL = 0x2409000c  # addiu t1, zero, 12: reveal count, not font size
CAPACITY = 22
PATCHED = 0x24090000 | CAPACITY


def verify(elf):
    require(u32(elf, file_offset(ADDRESS)) == PATCHED, 'Speaker draw count not updated')
    require(u32(elf, file_offset(0x201af8)) == jal(0x26f1a0), 'Speaker renderer call changed')
    require(u32(elf, file_offset(0x20153c)) == 0x24080032, 'Speaker allocation no longer holds 50 glyphs')
    require(u32(elf, file_offset(0x201540)) == jal(0x1d03b0), 'Speaker allocator call changed')
    require(u32(elf, file_offset(0x1d03e0)) == jal(0x1c8950), 'Speaker allocator sizing changed')
    return dict(glyphs_before=12,glyphs_after=CAPACITY,allocation_glyphs=50,
                allocation_unchanged=True,font_size_unchanged=True,address=hex(ADDRESS))


def patch(elf, report):
    require(u32(elf, file_offset(ADDRESS)) == ORIGINAL, 'Unexpected speaker draw instruction')
    struct.pack_into('<I',elf,file_offset(ADDRESS),PATCHED)
    report['speaker_capacity']=verify(elf)
