"""Audit original/translated PSS cadence and picture-start SCR headroom offline.

Usage: py -3.11 tools/verify_movie_timing.py ORIGINAL.PSS TRANSLATED.PSS --out REPORT.json
Requires ffprobe. This is not a PS2 decoder or emulator frame-time measurement.
Negative headroom is a scheduling risk, not proof of an observed playback stall.
"""
import argparse
import bisect
import collections
import hashlib
import json
import mmap
from pathlib import Path
import struct
import subprocess
import tempfile


def timestamp(b):
    return ((b[0] >> 1) & 7) << 30 | b[1] << 22 | (b[2] >> 1) << 15 | b[3] << 7 | b[4] >> 1


def scr_base(b):
    return (((b[0] >> 3) & 7) << 30 | (b[0] & 3) << 28 | b[1] << 20 |
            ((b[2] >> 3) & 31) << 15 | (b[2] & 3) << 13 | b[3] << 5 | b[4] >> 3)


def audit(path, cache):
    packets, offset, pos, scr = [], 0, 0, 0
    nonvideo = hashlib.sha256()
    with path.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data, cache.open('wb') as es:
        while pos < len(data):
            assert data[pos:pos + 3] == b'\0\0\1', 'PSS sync lost'
            sid = data[pos + 3]
            if sid == 0xb9:
                nonvideo.update(data[pos:])
                break
            if sid == 0xba:
                scr = scr_base(data[pos + 4:pos + 10])
                end = pos + 14 + (data[pos + 13] & 7)
            else:
                end = pos + 6 + struct.unpack_from('>H', data, pos + 4)[0]
            if sid == 0xe0:
                start = pos + 9 + data[pos + 8]
                flags = data[pos + 7] >> 6
                pts = timestamp(data[pos + 9:pos + 14]) if flags & 2 else None
                dts = timestamp(data[pos + 14:pos + 19]) if flags == 3 else None
                packets.append((offset, end - start, scr, pts, dts))
                es.write(data[start:end])
                offset += end - start
            else:
                nonvideo.update(data[pos:end])
            pos = end
    starts = [p[0] for p in packets]
    pictures, extensions, gops = [], collections.Counter(), 0
    with cache.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        pos, base = 0, 0
        while True:
            pos = data.find(b'\0\0\1', pos)
            if pos < 0:
                break
            code = data[pos + 3]
            if code == 0xb8:
                base = len(pictures)
                gops += 1
            elif code == 0:
                tr = data[pos + 4] << 2 | data[pos + 5] >> 6
                kind = (data[pos + 5] >> 3) & 7
                packet = packets[bisect.bisect_right(starts, pos) - 1]
                pictures.append((base + tr, kind, packet))
            elif code == 0xb5 and data[pos + 4] >> 4 == 8:
                bits = ''.join(format(x, '08b') for x in data[pos + 4:pos + 9])
                extensions['top_field_first=%s repeat_first_field=%s progressive_frame=%s picture_structure=%s' %
                           (bits[24], bits[30], bits[32], bits[22:24])] += 1
            pos += 4
    pts_bases = collections.Counter(p[2][3] - p[0] * 3003 for p in pictures if p[2][3] is not None)
    dts_bases = collections.Counter(p[2][4] - i * 3003 for i, p in enumerate(pictures) if p[2][4] is not None)
    assert pts_bases and dts_bases, 'No timestamps'
    pts0, dts0 = pts_bases.most_common(1)[0][0], dts_bases.most_common(1)[0][0]
    late = []
    for i, (display, kind, packet) in enumerate(pictures):
        deadline = dts0 + i * 3003
        if packet[2] > deadline:
            late.append(dict(display_frame=display, seconds=round(display * 1001 / 30000, 6),
                             picture_type='xIPB'[kind], start_after_decode_time_ms=(packet[2] - deadline) / 90))
    decoded = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_frames', '-show_entries',
        'frame=pts,repeat_pict,interlaced_frame', '-of', 'json', str(path)]))['frames']
    deltas = collections.Counter(b['pts'] - a['pts'] for a, b in zip(decoded, decoded[1:]))
    return dict(file=str(path), picture_count=len(pictures), gop_count=gops,
                display_indices_complete=sorted(p[0] for p in pictures) == list(range(len(pictures))),
                pts_bases=dict(pts_bases), dts_bases=dict(dts_bases),
                missing_pts=sum(p[2][3] is None for p in pictures),
                picture_extensions=dict(extensions), decoded_frame_count=len(decoded),
                decoded_pts_deltas=dict(deltas), repeat_picture_counts=dict(collections.Counter(p['repeat_pict'] for p in decoded)),
                nonvideo_sha256=nonvideo.hexdigest(), picture_starts_after_decode_time=late,
                scr_note='SCR is the pack clock, not measured disc arrival or emulator presentation time. '
                         'No end-of-picture lateness is inferred from padding or the next picture start.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('translated', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'work/source'
    with tempfile.TemporaryDirectory(prefix='movie-timing-', dir=root) as folder:
        original = audit(args.original, Path(folder) / 'original.m2v')
        translated = audit(args.translated, Path(folder) / 'translated.m2v')
    checks = {
        'same_frame_count': original['picture_count'] == translated['picture_count'],
        'same_nonvideo_bytes': original['nonvideo_sha256'] == translated['nonvideo_sha256'],
        'same_timestamp_bases': all(len(v['pts_bases']) == len(v['dts_bases']) == 1 for v in (original, translated)) and
                                original['pts_bases'].keys() == translated['pts_bases'].keys() and
                                original['dts_bases'].keys() == translated['dts_bases'].keys(),
        'constant_cadence_both': all(list(v['decoded_pts_deltas']) == [3003] for v in (original, translated)),
        'complete_frames_both': all(v['display_indices_complete'] and v['decoded_frame_count'] == v['picture_count'] and
                                   v['missing_pts'] == 0 for v in (original, translated)),
    }
    report = dict(original=original, translated=translated, checks=checks, runtime_verified=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(checks, indent=2))
    print('Picture starts after decode clock:', len(original['picture_starts_after_decode_time']),
          'original,', len(translated['picture_starts_after_decode_time']), 'translated')
    assert all(checks.values()), 'Movie cadence/structure check failed; see report'


if __name__ == '__main__':
    main()
