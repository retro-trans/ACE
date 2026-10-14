"""Export the disc's FMV movies (PSS) to MP4 for viewing: H.264 video at 4:3 (640x480) and the PCM soundtrack.

    python tools/movie_export.py [--built] [MOVIE001 M1_MOVIE001 ...]   # default: all 26 originals

Writes work/output/mp4/<name>.mp4 (originals) or work/output/mp4/built/<name>.mp4 (--built: the translated PSS
from work/output/movies). PSS audio is private stream 1: each payload starts with a 4-byte substream header; the
stream opens with "SShd" (format 1 = 16-bit PCM, rate, channels, interleave) and "SSbd" + size, and the samples
are interleaved per channel in blocks of `interleave` bytes.
"""
import struct
import subprocess
import sys
import wave
import movie_text as mt

NAMES = ['MOVIE001', 'MOVIE002', 'MOVIE003', 'MOVIE005'] + ['M1_MOVIE%03d' % i for i in range(1, 23)]


def audio(pss, wav):
    data = open(pss, 'rb').read()
    raw, i = bytearray(), 0
    while i < len(data) - 4:
        if data[i:i + 4] == b'\0\0\1\xba':
            i += 14 + (data[i + 13] & 7)
            continue
        sid = data[i + 3]
        if sid == 0xb9:
            break
        length = struct.unpack_from('>H', data, i + 4)[0]
        if sid == 0xbd:
            p = i + 9 + data[i + 8]
            raw += data[p + 4:i + 6 + length]
        i += 6 + length
    if raw[:4] != b'SShd':
        return False
    size, fmt, rate, channels, interleave = struct.unpack_from('<5I', raw, 4)
    body = raw[8 + size:]
    if body[:4] != b'SSbd':
        return False
    total = struct.unpack_from('<I', body, 4)[0]
    pcm = bytes(body[8:8 + total])
    if fmt != 1:
        raise SystemExit('%s: audio format %d is not PCM' % (pss, fmt))
    block = interleave * channels
    pcm = pcm[:len(pcm) // block * block]
    out = bytearray(len(pcm))
    frames = interleave // 2
    for b in range(0, len(pcm), block):
        for c in range(channels):
            chunk = pcm[b + c * interleave:b + (c + 1) * interleave]
            for k in range(frames):
                o = b + (k * channels + c) * 2
                out[o:o + 2] = chunk[2 * k:2 * k + 2]
    with wave.open(str(wav), 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(out))
    return True


def export(name, built=False):
    pss = (mt.OUT / (name + '.PSS')) if built else mt.source_movie(name)
    folder = mt.ROOT / 'work/output/mp4' / ('built' if built else '')
    folder.mkdir(parents=True, exist_ok=True)
    wav = mt.CACHE / (name + ('.built' if built else '') + '.wav')
    has_audio = audio(pss, wav)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(pss)]
    if has_audio:
        cmd += ['-i', str(wav)]
    cmd += ['-map', '0:v:0'] + (['-map', '1:a:0'] if has_audio else []) + [
        '-vf', 'scale=640:480:flags=lanczos,setsar=1', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
        '-pix_fmt', 'yuv420p'] + (['-c:a', 'aac', '-b:a', '192k'] if has_audio else []) + [
        '-movflags', '+faststart', str(folder / (name + '.mp4'))]
    subprocess.run(cmd, check=True)
    print(name, 'audio' if has_audio else 'no audio', '->', folder / (name + '.mp4'))


if __name__ == '__main__':
    built = '--built' in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or NAMES
    for n in names:
        export(n, built)
