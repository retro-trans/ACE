"""Read-only ACE movie-queue sampling through PCSX2 PINE; no input or writes.

Run while the supplied credits state is playing:
  python tools/trace_movie_playback.py --seconds 180 --out work/ui/credits-stutter/live

The sampled decoder counters are not host presentation timestamps. Polling can
miss transitions, and an empty queue between pictures is not itself a stall.
"""
import argparse
import csv
import json
import socket
import struct
import time
from pathlib import Path


class Pine:
    def __init__(self, port):
        self.sock = socket.create_connection(('127.0.0.1', port), timeout=2)

    def receive(self, count):
        chunks = bytearray()
        while len(chunks) < count:
            part = self.sock.recv(count - len(chunks))
            if not part:
                raise ConnectionError('PINE disconnected')
            chunks.extend(part)
        return bytes(chunks)

    def query(self, payload):
        self.sock.sendall(struct.pack('<I', len(payload) + 4) + payload)
        size = struct.unpack('<I', self.receive(4))[0]
        if not 5 <= size <= 1024 * 1024:
            raise ValueError('Invalid PINE reply length')
        reply = self.receive(size - 4)
        if reply[0] != 0:
            raise RuntimeError('PINE rejected the read; is a game loaded?')
        return reply[1:]

    def words(self, addresses):
        if not all(0 <= a <= 0x1fffffc for a in addresses):
            raise ValueError('Refusing a read outside EE RAM')
        reply = self.query(b''.join(b'\x02' + struct.pack('<I', a) for a in addresses))
        return struct.unpack('<%dI' % len(addresses), reply)

    def string(self, opcode):
        reply = self.query(bytes([opcode]))
        count = struct.unpack_from('<I', reply)[0]
        return reply[4:4 + count].rstrip(b'\0').decode('utf-8', errors='replace')


def ram_pointer(value):
    return 0x100000 <= value < 0x1ffe000 and value % 4 == 0


def sample(pine):
    state, obj = pine.words([0x33b118, 0x2c95c4])
    if state != 3 or not ram_pointer(obj):
        return None
    decoder, producer, queued, capacity = pine.words(
        [obj + 0x68, obj + 0xdc, obj + 0xe0, obj + 0xe4])
    if not ram_pointer(decoder) or capacity != 2 or queued > 2 or producer >= 2:
        return None
    count, picture = pine.words([decoder + 4, decoder + 0x130])
    return [obj, decoder, producer, queued, count, picture]


def run(args):
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pine = Pine(args.port)
    identity = dict(emulator=pine.string(8), game=pine.string(12), crc=pine.string(13))
    if identity['game'] != 'SLPS-25394':
        raise ValueError('Refusing to trace another game: ' + identity['game'])
    started = time.perf_counter()
    last_counter = None
    last_change = None
    first_counter = None
    gaps = []
    samples = skipped = empty = 0
    max_poll_gap = 0
    previous_poll = 0
    error = None
    try:
        with args.out.with_suffix('.csv').open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['elapsed_s', 'read_ms', 'object', 'decoder', 'producer',
                             'queued', 'decoder_count', 'picture_count'])
            while time.perf_counter() - started < args.seconds:
                before = time.perf_counter()
                row = sample(pine)
                elapsed = time.perf_counter() - started
                max_poll_gap = max(max_poll_gap, elapsed - previous_poll)
                previous_poll = elapsed
                if row is None:
                    skipped += 1
                else:
                    samples += 1
                    empty += row[3] == 0
                    writer.writerow([round(elapsed, 6), round((time.perf_counter() - before) * 1000, 3)] + row)
                    counter = (row[1], row[4])
                    if first_counter is None:
                        first_counter = counter
                    if counter != last_counter:
                        if last_change is not None and counter[0] == last_counter[0]:
                            gap = elapsed - last_change
                            if gap > 0.050:
                                gaps.append(dict(at_s=round(elapsed, 6), gap_ms=round(gap * 1000, 3),
                                                 counter_step=counter[1] - last_counter[1], queued=row[3]))
                        last_counter, last_change = counter, elapsed
                time.sleep(args.interval_ms / 1000)
    except (OSError, RuntimeError, ValueError) as exc:
        error = str(exc)
    finally:
        pine.sock.close()
    report = dict(**identity, elapsed_s=time.perf_counter() - started, samples=samples,
                  skipped_samples=skipped, empty_queue_samples=empty,
                  first_decoder_counter=first_counter, last_decoder_counter=last_counter,
                  final_counter_unchanged_ms=(time.perf_counter() - started - last_change) * 1000
                  if last_change is not None else None,
                  maximum_poll_gap_ms=max_poll_gap * 1000,
                  decoder_counter_gaps_over_50ms=gaps, error=error,
                  limitation='Read-only sampling, not a frame-present trace. Gaps include host scheduling and pauses; '
                             'queue emptiness alone is not proof of starvation.')
    args.out.with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=28011)
    parser.add_argument('--seconds', type=float, default=180)
    parser.add_argument('--interval-ms', type=float, default=5)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.seconds <= 0 or args.interval_ms < 2:
        parser.error('Use a positive duration and an interval of at least 2 ms')
    run(args)
