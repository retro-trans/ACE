"""Execute the native speaker draw wrapper and check all translated names."""
import argparse
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS64, UC_MODE_LITTLE_ENDIAN
from unicorn import mips_const as r
from ace_formats import ROOT, SOURCE_ISO, require
from font_upload import file_offset
from verify_dialogue_buffer import elf_from_iso
from speaker_capacity import patch, verify, ADDRESS, CAPACITY
import ui_layout as ui
from vwf_font import render


def draw_arguments(elf):
    cpu=Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 | UC_MODE_LITTLE_ENDIAN)
    cpu.mem_map(0x100000,0x300000)
    cpu.mem_write(0x201a70,elf[file_offset(0x201a70):file_offset(0x201b10)])
    widget,layout,state,text=0x300000,0x301000,0x302000,0x303000
    def word(at,value):
        cpu.mem_write(at,struct.pack('<I',value))
    word(widget+0x84,layout);word(widget+0x90,state)
    word(widget+0x8c,0x310000);word(widget+0x88,4096)
    word(layout+0x64,1);word(layout+0x80,13)
    word(state+0x1c,text)
    cpu.mem_write(text,b'Titans Soldier\0')
    cpu.reg_write(r.UC_MIPS_REG_A0,widget)
    cpu.reg_write(r.UC_MIPS_REG_SP,0x3ff000)
    cpu.reg_write(r.UC_MIPS_REG_RA,0x100000)
    cpu.emu_start(0x201a70,0x26f1a0,count=100)
    require(cpu.reg_read(r.UC_MIPS_REG_PC)==0x26f1a0,'Speaker wrapper did not reach renderer')
    # Numeric register indices avoid ABI alias differences for t1/t3 in MIPS64.
    result=dict(count=cpu.reg_read(r.UC_MIPS_REG_9),text=cpu.reg_read(r.UC_MIPS_REG_11),
                font_size_bits=cpu.reg_read(r.UC_MIPS_REG_F12),
                font_selection=cpu.reg_read(r.UC_MIPS_REG_8))
    require(result['text']==text and result['font_selection']==1,'Name/font arguments changed')
    require(result['font_size_bits']==struct.unpack('<I',struct.pack('<f',13.0))[0],'Font size changed')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iso',type=Path)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    stock=elf_from_iso(SOURCE_ISO)
    candidate=bytearray(stock)
    patch(candidate,{})
    require([i for i,(a,b) in enumerate(zip(stock,candidate)) if a!=b]==[file_offset(ADDRESS)],'Unexpected patch bytes')
    elf=elf_from_iso(args.iso) if args.iso else bytes(candidate)
    report=verify(elf)
    before,after=draw_arguments(stock),draw_arguments(elf)
    require(before['count']==12 and after['count']==CAPACITY,'Incorrect native draw count')
    group=ui.load('speakers');font=ui.font(group['font'])
    require(group['limits']['bytes']<=CAPACITY,'Speaker translation budget exceeds draw cap')
    affected=[]
    for row in group['rows']:
        text=row['en']
        require(not ui.problems(group,row),'Invalid speaker name: '+text)
        require(text.isascii() and len(text)<=CAPACITY<=50,'Speaker exceeds draw/allocation capacity')
        if len(text)>12:
            affected.append(dict(text=text,previously_visible=text[:12],glyphs=len(text),width=ui.width(font,text)))
    require(any(x['previously_visible']=='Titans Soldi' for x in affected),'Reported truncation not reproduced')
    report.update(labels_checked=len(group['rows']),affected=affected,native_wrapper_verified=True,runtime_verified=False)
    if args.write:
        dest=ROOT/'work/ui/speaker-capacity';dest.mkdir(parents=True,exist_ok=True)
        (dest/'capacity-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        render(font,['Titans Soldi','Titans Soldier'],scale=4,width=151).save(dest/'font-preview.png')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
