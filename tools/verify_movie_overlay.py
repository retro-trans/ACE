"""Execute the actual overlay hooks in a MIPS64 CPU and audit picture writes.

This tests injected machine code, not a second implementation of its control
flow. It does not substitute for a fresh-boot PCSX2/hardware playback test.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

import numpy as np
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS64, UC_MODE_LITTLE_ENDIAN
from unicorn import mips_const as regs
from PIL import Image, ImageDraw
from ace_formats import ROOT, SOURCE_ISO, iso_files, require, u32
import movie_overlay as mo
import movie_text as mt

VIEW = ROOT / 'work/ui/movie-overlay'
RING = 0x700000
BUFFER = 0x20800000
FRAME = mo.W * mo.H * 4


def load_elf(cpu, elf):
    phoff, phsize, phnum = u32(elf, 28), struct.unpack_from('<H', elf, 42)[0], struct.unpack_from('<H', elf, 44)[0]
    for i in range(phnum):
        kind, at, va, _, size, mem, _, _ = struct.unpack_from('<8I', elf, phoff + i * phsize)
        if kind == 1:
            cpu.mem_write(va, elf[at:at + size] + bytes(mem - size))


def decode_pixels(payload, address, size):
    """Unpack independent expected pixels; reject out-of-range stream writes."""
    mask = np.zeros(mo.W * mo.H, bool)
    values = np.zeros(mo.W * mo.H, np.uint32)
    pos, end = address - mo.BASE, address - mo.BASE + size
    while pos < end:
        header = u32(payload, pos)
        at, count = header & 0x3ffff, header >> 18
        pos += 4
        stop = pos + count
        require(stop <= end, 'Pixel stream chunk overrun')
        while pos < stop:
            value = payload[pos]
            pos += 1
            n = 1
            if value == 255:
                require(pos + 2 <= stop, 'Truncated pixel run')
                n, value = payload[pos:pos + 2]
                pos += 2
            require(n > 0 and at + n <= len(mask), 'Pixel run exceeds frame')
            require(not mask[at:at + n].any(), 'Overlapping packed pixel runs')
            mask[at:at + n] = True
            values[at:at + n] = value
            at += n
        pos = (pos + 3) & ~3
    require(pos == end, 'Pixel stream size mismatch')
    return mask, values


def audit(elf, summary):
    payload_at = summary['elf_payload_offset']
    payload = elf[payload_at:payload_at + summary['payload_bytes']]
    require(hashlib.sha256(payload).hexdigest() == summary['sha256'], 'ELF overlay payload differs')
    cpu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 | UC_MODE_LITTLE_ENDIAN)
    cpu.mem_map(0x100000, 0x1f00000)
    cpu.mem_map(BUFFER - 4096, 2 * FRAME + 8192)
    load_elf(cpu, elf)
    sentinel = b'\xa7' * 4096
    cpu.mem_write(BUFFER - 4096, sentinel)
    cpu.mem_write(BUFFER + 2 * FRAME, sentinel)
    register_ids = [getattr(regs, 'UC_MIPS_REG_S%d' % i) for i in range(8)] + [regs.UC_MIPS_REG_GP, regs.UC_MIPS_REG_FP]
    saved = [0x1234567800000000 + i * 0x12345 for i in range(len(register_ids))]
    # s0 is the queue pointer at the real callsite.
    saved[0] = RING
    for r, value in zip(register_ids, saved):
        cpu.reg_write(r, value)
    cpu.reg_write(regs.UC_MIPS_REG_SP, 0x1e00000)
    reference = (np.arange(mo.W * mo.H, dtype=np.uint32) * 1234567) ^ np.uint32(0x80abcdef)
    background = reference.astype('<u4').tobytes()
    state_checks = frame_checks = pixel_checks = 0

    def open_movie(group, movie):
        cpu.reg_write(regs.UC_MIPS_REG_A0, group)
        cpu.reg_write(regs.UC_MIPS_REG_A1, movie)
        cpu.reg_write(regs.UC_MIPS_REG_SP, 0x1e00000)
        cpu.reg_write(regs.UC_MIPS_REG_RA, 0x123456)
        cpu.emu_start(mo.OPEN, mo.OPEN + 8, count=1000)
        require(cpu.reg_read(regs.UC_MIPS_REG_PC) == mo.OPEN + 8, 'Open hook did not resume')
        require(cpu.reg_read(regs.UC_MIPS_REG_SP) == 0x1e00000 - 0x110, 'Displaced stack prologue differs')
        require(cpu.reg_read(regs.UC_MIPS_REG_A0) == group and cpu.reg_read(regs.UC_MIPS_REG_A1) == movie,
                'Movie arguments changed')
        require(cpu.reg_read(regs.UC_MIPS_REG_A2) == group, 'Displaced argument move differs')
        require(cpu.reg_read(regs.UC_MIPS_REG_RA) == 0x123456, 'Open hook changed return address')
        return struct.unpack('<2I', cpu.mem_read(mo.STATE, 8))

    def render(n, index, expected, dims=(mo.W, mo.H)):
        nonlocal frame_checks, pixel_checks
        ring = bytearray(0x30)
        struct.pack_into('<5I', ring, 0, BUFFER, index, 0, 2, mo.W * mo.H)
        struct.pack_into('<2I', ring, 0x24, *dims)
        cpu.mem_write(RING, bytes(ring))
        cpu.mem_write(mo.STATE + 4, struct.pack('<I', n))
        cpu.mem_write(BUFFER, background)
        cpu.mem_write(BUFFER + FRAME, background)
        cpu.emu_start(mo.QUEUE, 0x1f2e10, count=2000000)
        require(cpu.reg_read(regs.UC_MIPS_REG_PC) == 0x1f2e10, 'Hook failed to publish / instruction limit')
        require(cpu.reg_read(regs.UC_MIPS_REG_A0) == RING, 'Queue argument was clobbered')
        require(cpu.reg_read(regs.UC_MIPS_REG_RA) == mo.QUEUE + 8, 'Queue return address was clobbered')
        require(bytes(cpu.mem_read(RING, len(ring))) == ring, 'Hook altered original ring bookkeeping')
        for r, value in zip(register_ids, saved):
            require(cpu.reg_read(r) == value, 'Callee-saved register clobbered')
        for i in (0, 1):
            wanted = expected if i == index else reference
            got = np.frombuffer(cpu.mem_read(BUFFER + i * FRAME, FRAME), dtype='<u4')
            require(np.array_equal(got, wanted), 'Pixel mismatch at picture %d, ring %d' % (n, i))
        require(cpu.mem_read(BUFFER - 4096, 4096) == sentinel and
                cpu.mem_read(BUFFER + 2 * FRAME, 4096) == sentinel, 'Frame buffer guard overwritten')
        frame_checks += 1
        pixel_checks += 2 * mo.W * mo.H

    for movie in summary['movies']:
        number = int(movie['movie'][-3:])
        table, n = open_movie(1, number)
        require(table == u32(payload, mo.DIRECTORY - mo.BASE + number * 4) and n == 0, 'Movie reset mismatch')
        state_checks += 1
        cards = []
        spec_path = mt.SPEC / (movie['movie'] + '.en.json')
        require(hashlib.sha256(spec_path.read_bytes()).hexdigest() == movie['source_spec_sha256'],
                'Caption source has changed since compilation')
        specs = json.loads(spec_path.read_text(encoding='utf-8'))['segments']
        es, _ = mt.elementary(movie['movie'])
        for i in range(u32(payload, table - mo.BASE)):
            a, b, pixels, length, fade, ident = struct.unpack_from('<6I', payload, table - mo.BASE + 4 + i * 24)
            mask, gray = decode_pixels(payload, pixels, length)
            fades = np.frombuffer(payload[fade - mo.BASE:fade - mo.BASE + (b - a) * 2], dtype='<u2')
            require(len(fades) == b - a and int(fades.max()) <= 256, 'Invalid opacity table')
            k, spec = next((k, s) for k, s in enumerate(specs) if s['card'] == ident)
            source = mt.StaticCard(movie['movie'], es, k, spec)
            require(spec['frames'] == [a, b], 'Compiled caption timing differs from source')
            require(np.array_equal(mo.untiled(mask), mt.dilate(source.ink, 4) | (source.text > 0)),
                    'Compiled erase/text coverage differs from source')
            source_gray = np.rint(source.text * (spec['colour'][0] - 16) * 255 / 219).clip(0, 255).astype(np.uint8)
            require(np.array_equal(mo.untiled(gray), source_gray), 'Compiled glyph antialiasing differs')
            require(np.array_equal(fades, np.rint(np.clip(source.energy / source.peak, 0, 1) * 256)),
                    'Compiled fade timing differs from source')
            cards.append((a, b, mask, gray, fades, ident))
        # Both exact boundaries, all card midpoints and opacity extrema. These
        # include adjacent captions, blank gaps, full opacity and faint fades.
        frames = {0}
        for a, b, mask, gray, fades, ident in cards:
            frames.update((max(0, a - 1), a, (a + b) // 2, b - 1, b, a + int(np.argmax(fades))))
        for test, n in enumerate(sorted(frames)):
            expected = reference.copy()
            active = [row for row in cards if row[0] <= n < row[1]]
            require(len(active) <= 1, 'Overlapping captions')
            if active:
                a, b, mask, gray, fades, ident = active[0]
                c = gray[mask] * int(fades[n - a]) >> 8
                expected[mask] = 0x80000000 | c | c << 8 | c << 16
            render(n, test % 2, expected)
            require(u32(cpu.mem_read(mo.STATE + 4, 4), 0) == n + 1, 'Frame counter mismatch')
        # Reopening resets timing, including replay of the same movie.
        require(open_movie(1, number)[1] == 0, 'Replay did not reset caption clock')
        state_checks += 1
        print(movie['movie'], len(frames), 'CPU frame checks passed', flush=True)

    for group, number in ((0, 1), (0, 2), (0, 3), (0, 5), (1, 0), (1, 23), (2, 1)):
        require(open_movie(group, number) == (0, 0), 'Non-story movie enabled overlay')
        render(500, 0, reference)
        require(u32(cpu.mem_read(mo.STATE + 4, 4), 0) == 500, 'Disabled overlay advanced clock')
        state_checks += 1
    open_movie(1, 1)
    render(80, 0, reference, dims=(640, 448))
    render(80, 0, reference, dims=(512, 480))
    render(80, 2, reference)
    # All four heap entry points must agree, while original BSS clearing must
    # stop before the payload. New memory is a real ELF PT_LOAD, not a cave.
    new_end = mo.BASE + len(payload)
    for hi, lo in ((0x1001d0, 0x1001d8), (0x12bee4, 0x12bef0), (0x12bf54, 0x12bf60)):
        low = struct.unpack_from('<h', elf, mo.off(lo))[0]
        require((u32(elf, mo.off(hi)) & 65535) * 65536 + low == new_end, 'Heap overlaps payload')
    require(u32(elf, mo.off(0x2a12d4)) == new_end, 'libc sbrk overlaps payload')
    require(u32(elf, mo.off(0x100120)) == 0x3c030035 and
            u32(elf, mo.off(0x100128)) == 0x2463a480, 'BSS clear would damage payload')
    return {'payload_bytes': len(payload), 'card_count': summary['card_count'],
            'cpu_frame_checks': frame_checks, 'framebuffer_pixel_comparisons': pixel_checks,
            'movie_state_checks': state_checks, 'all_checks_passed': True,
            'heap_start': hex(new_end), 'outside_overlay_and_other_buffer_unchanged': True,
            'callee_saved_registers_and_queue_bookkeeping_preserved': True,
            'runtime_playback_verified': False}


def previews(elf):
    """Render actual compiled code onto original decoded frames for visual QA."""
    cpu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS64 | UC_MODE_LITTLE_ENDIAN)
    cpu.mem_map(0x100000, 0x1f00000)
    cpu.mem_map(BUFFER, 2 * FRAME)
    load_elf(cpu, elf)
    cpu.reg_write(regs.UC_MIPS_REG_S0, RING)
    paths = []
    for movie, frame in ((1, 80), (2, 250), (11, 795)):
        name = 'M1_MOVIE%03d' % movie
        es, _ = mt.elementary(name)
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(es),
                                      '-vf', 'select=eq(n\\,%d)' % frame, '-frames:v', '1',
                                      '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'])
        rgba = np.frombuffer(raw, np.uint8).reshape(mo.H, mo.W, 4).copy()
        rgba[:, :, 3] = 128
        before = rgba.copy()
        tiled = rgba.reshape(mo.H // 16, 16, mo.W // 16, 16, 4).transpose(2, 0, 1, 3, 4).copy()
        cpu.reg_write(regs.UC_MIPS_REG_A0, 1)
        cpu.reg_write(regs.UC_MIPS_REG_A1, movie)
        cpu.reg_write(regs.UC_MIPS_REG_SP, 0x1e00000)
        cpu.emu_start(mo.OPEN, mo.OPEN + 8, count=1000)
        cpu.mem_write(mo.STATE + 4, struct.pack('<I', frame))
        ring = bytearray(0x30)
        struct.pack_into('<5I', ring, 0, BUFFER, 0, 0, 2, mo.W * mo.H)
        struct.pack_into('<2I', ring, 0x24, mo.W, mo.H)
        cpu.mem_write(RING, bytes(ring))
        cpu.mem_write(BUFFER, tiled.tobytes())
        cpu.emu_start(mo.QUEUE, 0x1f2e10, count=2000000)
        require(cpu.reg_read(regs.UC_MIPS_REG_PC) == 0x1f2e10, 'Preview hook did not complete')
        after = np.frombuffer(cpu.mem_read(BUFFER, FRAME), np.uint8).reshape(mo.W // 16, mo.H // 16, 16, 16, 4)
        after = after.transpose(1, 2, 0, 3, 4).reshape(mo.H, mo.W, 4)
        image = Image.fromarray(after[:, :, :3])
        path = VIEW / ('%s-f%d.png' % (name, frame))
        image.save(path)
        side = Image.new('RGB', (mo.W * 2, mo.H + 24))
        side.paste(Image.fromarray(before[:, :, :3]), (0, 24))
        side.paste(image, (mo.W, 24))
        draw = ImageDraw.Draw(side)
        draw.text((8, 4), 'Original video', fill='white')
        draw.text((mo.W + 8, 4), 'Runtime overlay (CPU test)', fill='white')
        side.save(path.with_name(path.stem + '-comparison.png'))
        paths.append(str(path.relative_to(ROOT)))
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iso', type=Path)
    args = ap.parse_args()
    if args.iso:
        with args.iso.open('rb') as f:
            rec = iso_files(f)['/SLPS_253.94']
            f.seek(rec['offset'])
            elf = f.read(rec['size'])
        summary = json.loads(args.iso.with_suffix('.json').read_text(encoding='utf-8'))['movie_overlay']
    else:
        with SOURCE_ISO.open('rb') as f:
            rec = iso_files(f)['/SLPS_253.94']
            f.seek(rec['offset'])
            source = f.read(rec['size'])
        report = {}
        elf = mo.patch_elf(source, report)
        summary = report['movie_overlay']
        (mo.OUT / 'test.elf').write_bytes(elf)
    report = audit(elf, summary)
    VIEW.mkdir(parents=True, exist_ok=True)
    report['previews'] = previews(elf)
    (VIEW / 'cpu-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
