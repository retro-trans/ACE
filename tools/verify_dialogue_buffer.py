"""Check the operator allocation and optionally inspect the reported 0.1.31 state.

State inputs are read-only, locally extracted eeMemory.bin and PCSX2 Internal
Structures.dat from PCSX2 2.8.2. Do not commit those copyrighted game extracts.
This checks saved memory and allocation capacity, not a running emulator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from ace_formats import ROOT, SOURCE_ISO, iso_files, require, u32
from dialogue_buffer import allocation, patch, verify, CAPACITY
from font_upload import HUD_REFRESH_GATES, HUD_UPLOAD_CALLS, SWIZZLED_UPLOAD, jal
import dialogue_layout as layout


def elf_from_iso(path):
    with path.open('rb') as f:
        e = iso_files(f)['/SLPS_253.94']
        f.seek(e['offset'])
        return f.read(e['size'])


def snapshot(folder, elf):
    ram = (folder / 'eeMemory.bin').read_bytes()
    internal = (folder / 'PCSX2 Internal Structures.dat').read_bytes()
    require(len(ram) == 32 * 1024 * 1024, 'Unexpected EE RAM size')
    require(u32((folder / 'PCSX2 Savestate Version.id').read_bytes(), 0) == 0x9a590000,
            'Unsupported PCSX2 state layout')
    require(all(u32(ram, a) == 0 for a in HUD_REFRESH_GATES) and
            all(u32(ram, a) == jal(SWIZZLED_UPLOAD) for a in HUD_UPLOAD_CALLS),
            'Expected 0.1.31 font instruction signatures')
    base = internal.index(b'cpuRegs' + bytes(25)) + 32
    gp = u32(internal, base + 28 * 16)
    pc = u32(internal, base + 680)
    message = u32(ram, gp - 0x7b18)
    text = ram[message + 0x24:message + 0xa8].split(bytes(1))[0]
    typed = u32(ram, message + 0xa8)
    require(typed == len(text) == 53, 'Not the reported 53-character hang state')
    row_id = u32(ram, message + 0x10)
    row = next(r for r in layout.load('044')['rows'] if r['id'] == row_id)
    require(row['en'].encode('cp932') == text, 'Saved message differs from 044 translation')
    require(b'\\target\\snd\\Voice\\m044\\' in ram and
            b'mission\\m044\\scene00\\' in ram, 'Mission 044 resources missing')
    # Identify the active operator widget by its real update function and text
    # pointer; do not assume the heap addresses stay fixed between runs.
    widgets = []
    for m in re.finditer(re.escape(struct.pack('<I', 0x201940)), ram):
        obj = m.start() - 0xa4
        if obj < 0 or obj % 16:
            continue
        sub = u32(ram, obj + 0x90)
        if not 0 < sub < len(ram) - 0x50:
            continue
        if u32(ram, sub + 0x1c) == message + 0x24:
            widgets.append((obj, sub))
    require(len(widgets) == 1, 'Cannot uniquely identify the operator widget')
    obj, sub = widgets[0]
    packet = u32(ram, obj + 0x8c)
    reserved = u32(ram, sub + 0x28)
    used = u32(ram, obj + 0x88) * 16
    require(reserved == allocation(elf, 50), 'Unexpected original allocation')
    require(used == allocation(elf, typed), 'Unexpected actual drawing packet length')
    require(used - reserved == 336, 'Reported overflow not reproduced')
    # Decode the live packet until a tag requests more bytes than the packet
    # actually contains. Every healthy glyph before it consumes seven qwords.
    offset = glyphs = 0
    while offset + 16 <= used:
        lo, hi = struct.unpack_from('<QQ', ram, packet + offset)
        n, mode, regs = lo & 32767, lo >> 58 & 3, lo >> 60 or 16
        size = (n * regs * 16 if mode == 0 else
                ((n * regs + 1) // 2) * 16 if mode == 1 else n * 16)
        if offset + 16 + size > used:
            break
        if n == 2 and mode == 0 and regs == 3 and hi == 0x412:
            glyphs += 1
        offset += 16 + size
    require(glyphs == 53 and offset == 0x17d0, 'Unexpected saved packet damage')
    require(size == 0x425000, 'Unexpected malformed GIF tag')
    hw = (folder / 'eeHwRegs.bin').read_bytes()
    require(pc == 0x13d5f0 and u32(hw, 0x9000) & 0x100,
            'State is not waiting on the reported VIF1 transfer')
    return dict(ee_pc=hex(pc), mission='044', message_id=row_id,
                ram_sha256=hashlib.sha256(ram).hexdigest(),
                text_sha256=hashlib.sha256(text).hexdigest(), typed_glyphs=typed,
                widget=hex(obj), packet=hex(packet),
                allocated_bytes=reserved, emitted_bytes=used,
                overwritten_bytes=used-reserved, malformed_tag_offset=hex(offset),
                malformed_tag_requested_bytes=size,
                vif1_chcr=hex(u32(hw, 0x9000)), gif_stat=hex(u32(hw, 0x3020)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iso', type=Path)
    ap.add_argument('--state-dir', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    original = elf_from_iso(SOURCE_ISO)
    if args.iso:
        candidate = elf_from_iso(args.iso)
    else:
        candidate = bytearray(original)
        patch(candidate, {})
    report = verify(candidate)
    counts, oversized = [], []
    for mission in layout.missions():
        rows = layout.load(mission)['rows']
        windows = layout.windows(rows)
        for row in rows:
            if not row.get('en'):
                continue
            en = '\n'.join(layout.wrap(row['en'], layout.max_lines(windows[row['id']])))
            # Byte count is conservative for double-byte glyphs and controls.
            count = len(en.encode('cp932'))
            require(count <= CAPACITY, 'Translated message exceeds packet budget')
            counts.append(count)
            if windows[row['id']] == 'op' and count > 50:
                oversized.append(dict(mission=mission, row=row['id'], bytes=count))
    report.update(rows_checked=len(counts), maximum_visible_bytes=max(counts),
                  operator_rows_over_original_capacity=oversized)
    if args.state_dir:
        report['reported_state'] = snapshot(args.state_dir, original)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items()
                      if k != 'operator_rows_over_original_capacity'}, indent=2))
    print('Operator rows above old capacity:', len(oversized))


if __name__ == '__main__':
    main()
