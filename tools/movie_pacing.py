"""Move excessive MPEG video zero stuffing into program-stream padding packets.

No pictures are re-encoded. Pack clocks, picture PES timestamps, audio, original
packet boundaries and total file size are preserved. Validate decoded frame
hashes before using an output in a build. Requires only Python's standard library.
"""
import argparse
import bisect
import hashlib
import json
import mmap
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def verify_frames(source, target):
    """Compare every decoded pixel, frame timestamp and duration using FFmpeg."""
    with tempfile.TemporaryDirectory(prefix='ace-movie-pacing-') as folder:
        hashes = []
        for index, path in enumerate((source, target)):
            dest = Path(folder) / ('%d.framemd5' % index)
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-threads', '2',
                            '-i', str(path), '-map', '0:v:0', '-an', '-fps_mode', 'passthrough',
                            '-f', 'framemd5', str(dest)], check=True)
            hashes.append(dest.read_bytes())
        if hashes[0] != hashes[1]:
            raise ValueError('Repacking changed decoded pictures or timing')
        return dict(decoded_frames_verified=sum(not line.startswith(b'#') for line in hashes[0].splitlines()),
                    frame_md5_sha256=hashlib.sha256(hashes[0]).hexdigest())


def ready(movies, report):
    """Use separately verified pacing outputs, without changing the movie cache."""
    root = Path(__file__).resolve().parent.parent / 'work/output/movie-pacing'
    selected, evidence = {}, {}
    for name, path in movies.items():
        out = root / path.name
        meta = out.with_suffix('.pacing.json')
        if not meta.exists():
            raise ValueError('Prepare the pacing movie with --verify first: ' + path.name)
        entry = json.loads(meta.read_text(encoding='utf-8'))
        if not entry.get('decoded_frames_verified'):
            raise ValueError('Missing full decoded-frame verification: ' + path.name)
        if file_hash(path) != entry['source_sha256'] or file_hash(out) != entry['sha256']:
            raise ValueError('Pacing cache is stale: ' + path.name)
        selected[name], evidence[name] = out, entry
    report['movie_pacing'] = evidence
    return selected


def packets(data):
    pos = 0
    while pos < len(data) - 3:
        if data[pos:pos + 3] != b'\0\0\1':
            raise ValueError('PSS synchronization lost at %#x' % pos)
        sid = data[pos + 3]
        if sid == 0xb9:
            yield pos, len(data), sid, None
            return
        end = pos + (14 + (data[pos + 13] & 7) if sid == 0xba else
                     6 + struct.unpack_from('>H', data, pos + 4)[0])
        if end > len(data):
            raise ValueError('Truncated PSS packet')
        payload = pos + 9 + data[pos + 8] if sid == 0xe0 else None
        yield pos, end, sid, payload
        pos = end


def repack(source, target):
    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve():
        raise ValueError('Use a separate output; the input is never overwritten')
    with source.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        table = list(packets(data))
        es = b''.join(data[p:end] for start, end, sid, p in table if sid == 0xe0)
        # Keep eight leading zero bytes and the start code's two zero bytes.
        # Such long runs cannot be MPEG-2 VLC picture data. Only strip runs
        # immediately before picture/GOP/sequence boundaries, not arbitrary zeros.
        spans = [(m.start() + 8, m.end() - 2) for m in
                 re.finditer(b'\x00{64,}(?=\x01[\x00\xb3\xb7\xb8])', es)]
        del es
        ends = [b for a, b in spans]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        offset = moved = changed = padding_only = 0
        nonvideo = hashlib.sha256()
        with target.open('r+b') as out:
            for start, end, sid, p in table:
                if sid != 0xe0:
                    nonvideo.update(data[start:end])
                    continue
                size = end - p
                cursor = offset
                parts = []
                index = bisect.bisect_right(ends, offset)
                while index < len(spans) and spans[index][0] < offset + size:
                    a, b = spans[index]
                    a, b = max(a, offset), min(b, offset + size)
                    if a > cursor:
                        parts.append(data[p + cursor - offset:p + a - offset])
                    cursor = b
                    index += 1
                parts.append(data[p + cursor - offset:end])
                keep = b''.join(parts)
                removed = size - len(keep)
                offset += size
                if removed < 6:
                    continue
                if keep:
                    header = bytearray(data[start:p])
                    struct.pack_into('>H', header, 4, len(header) - 6 + len(keep))
                    replacement = bytes(header) + keep + b'\0\0\1\xbe' + struct.pack('>H', removed - 6) + b'\xff' * (removed - 6)
                else:
                    replacement = b'\0\0\1\xbe' + struct.pack('>H', end - start - 6) + b'\xff' * (end - start - 6)
                    padding_only += 1
                assert len(replacement) == end - start
                out.seek(start)
                out.write(replacement)
                moved += removed
                changed += 1
    # Check every original nonvideo range in place, including all audio and SCR.
    with source.open('rb') as f, target.open('rb') as g:
        for start, end, sid, p in table:
            if sid != 0xe0:
                f.seek(start); g.seek(start)
                assert f.read(end - start) == g.read(end - start)
    report = dict(source=str(source), output=str(target), bytes=target.stat().st_size,
                  stuffing_runs=len(spans), video_stuffing_bytes_removed=moved,
                  changed_video_packets=changed, padding_only_packets=padding_only,
                  original_nonvideo_sha256=nonvideo.hexdigest(),
                  original_nonvideo_ranges_identical=True, reencoded_pictures=0)
    report.update(source_sha256=file_hash(source), sha256=file_hash(target))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--verify', action='store_true', help='compare every decoded frame and timestamp')
    args = parser.parse_args()
    report = repack(args.source, args.output)
    if args.verify:
        report.update(verify_frames(args.source, args.output))
    args.output.with_suffix('.pacing.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
