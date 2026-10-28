"""Validate target-name capacity and execute its native allocation arithmetic."""
import argparse
import json
from pathlib import Path
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS64, UC_MODE_LITTLE_ENDIAN
from unicorn import mips_const as regs
from ace_formats import ROOT, SOURCE_ISO, require, u32
from verify_dialogue_buffer import elf_from_iso
from font_upload import file_offset
from lockon_capacity import patch, verify, CAPACITY, SITES
import ui_layout as ui
from vwf_font import render


def cpu_allocation(elf, count):
    cpu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 | UC_MODE_LITTLE_ENDIAN)
    cpu.mem_map(0x100000, 0x100000)
    cpu.mem_write(0x1c9220, elf[file_offset(0x1c9220):file_offset(0x1c9250)])
    cpu.reg_write(regs.UC_MIPS_REG_A0, count)
    cpu.reg_write(regs.UC_MIPS_REG_RA, 0x100000)
    cpu.emu_start(0x1c9220, 0x100000, count=30)
    require(cpu.reg_read(regs.UC_MIPS_REG_PC) == 0x100000, 'Allocator did not return')
    return cpu.reg_read(regs.UC_MIPS_REG_V0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iso', type=Path)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    source = elf_from_iso(SOURCE_ISO)
    expected = bytearray(source)
    patch(expected, {})
    differences = [i for i,(a,b) in enumerate(zip(source,expected)) if a != b]
    require(differences == sorted(file_offset(a) for a in SITES), 'Unexpected patch bytes')
    elf = elf_from_iso(args.iso) if args.iso else bytes(expected)
    report = verify(elf)
    group = ui.load('lockon')
    font = ui.font(group['font'])
    require(group['limits']['bytes'] <= CAPACITY and group['limits']['lines'] == 1,
            'Translation budget exceeds target renderer capacity')
    affected=[]
    packet_bytes = cpu_allocation(elf, CAPACITY)
    require(packet_bytes == report['bytes_after'], 'Allocation arithmetic mismatch')
    require(cpu_allocation(elf, 12) == report['bytes_before'], 'Original allocation mismatch')
    for row in group['rows']:
        text=row['en']
        require(not ui.problems(group,row), 'Invalid target label: '+text)
        require(text.isascii() and len(text) <= CAPACITY, 'Character capacity exceeded')
        require(cpu_allocation(elf,len(text)) <= packet_bytes, 'Target packet could overflow')
        if len(text)>12:
            affected.append(dict(text=text,previously_visible=text[:12],glyphs=len(text),width=ui.width(font,text)))
    require(any(r['previously_visible']=="Jonathan's G" for r in affected), 'Reported truncation not reproduced')
    # A changed allocation or draw instruction must be rejected, not silently accepted.
    for address,(original,_,_,_) in SITES.items():
        bad=bytearray(elf)
        bad[file_offset(address):file_offset(address)+4]=original.to_bytes(4,'little')
        try:
            verify(bad)
        except ValueError:
            pass
        else:
            raise ValueError('Accepted mismatched draw/allocation limits')
    report.update(labels_checked=len(group['rows']),affected=affected,
                  native_allocator_executed=True,font_size_unchanged=True,runtime_verified=False)
    if args.write:
        dest=ROOT/'work/ui/lockon-capacity'
        dest.mkdir(parents=True,exist_ok=True)
        (dest/'capacity-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        render(font,["Jonathan's G", "Jonathan's Grancher",'Psycho Gundam Mk-II'],scale=4,width=164).save(dest/'font-preview.png')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
