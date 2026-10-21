"""Check encoded story-movie fade edges for remaining Japanese strokes.

At every newly covered fade frame, inspect the source lettering pixels outside
the English glyphs/outline. The encoded result must leave that old-lettering area
dark. Also checks clean guard frames on either side. This supplements, not replaces,
packet/audio checks and in-game playback review.
"""
import argparse
import json
import numpy as np
import movie_text as mt
from ace_formats import require


def verify(movie):
    spec = json.loads((mt.SPEC / (movie + '.json')).read_text(encoding='utf-8'))
    timing = json.loads((mt.VIEW / 'subtitle-timing-0.1.28' / (movie + '.json')).read_text(encoding='utf-8'))
    report = json.loads((mt.OUT / (movie + '.json')).read_text(encoding='utf-8'))
    require(report['spec'] == mt.spec_hash(movie), 'Encoded movie is stale: ' + movie)
    original, _ = mt.elementary(movie)
    encoded = mt.OUT / (movie + '.PSS')
    total = report['frames']
    checks, english = [], {}
    for s in spec['segments']:
        require(s.get('timing_revision') == 'faint-fades-v1', 'Card lacks fade correction')
        a, b = s['frames']
        old_a, old_b = s['scan_frames']
        text, shadow = mt.Segment.render_lines(s, mt.H)
        english[s['card']] = mt.dilate((text + shadow) > 0.001, 4)
        mask = np.zeros((mt.H, mt.W), bool)
        x0, _, x1, _ = s['box']
        for y0, y1 in s['ink_rows']:
            mask[max(0, y0):min(mt.H, y1), x0:x1] = True
        checks.append(dict(s=s, mask=mask, wanted=set(range(max(0, a - 2), old_a + 2)) |
                          set(range(old_b - 2, min(total, b + 2))), checked=0, lit=0,
                          worst_residual=0, worst_frame=None))
    wanted = set().union(*(c['wanted'] for c in checks))
    failures = []
    decoded = 0
    for (n, src), (m, dst) in zip(mt.frames(original, 0, total), mt.frames(encoded, 0, total)):
        require(n == m, 'Decoded frame order differs')
        decoded += 1
        if n not in wanted:
            continue
        source = np.frombuffer(src, np.uint8, mt.W * mt.H).reshape(mt.H, mt.W)
        result = np.frombuffer(dst, np.uint8, mt.W * mt.H).reshape(mt.H, mt.W)
        allowed = np.zeros((mt.H, mt.W), bool)
        for s in spec['segments']:
            if s['frames'][0] <= n < s['frames'][1]:
                allowed |= english[s['card']]
        for c in checks:
            if n not in c['wanted']:
                continue
            c['checked'] += 1
            old_ink = c['mask'] & (source > 24) & ~allowed
            count = np.count_nonzero(old_ink)
            if count < 24:
                continue
            c['lit'] += 1
            residual = int(np.count_nonzero(old_ink & (result > 40)))
            if residual > c['worst_residual']:
                c['worst_residual'], c['worst_frame'] = residual, n
            # A few compression-ringing pixels are permitted; readable remnants
            # have hundreds/thousands of source-shaped strokes.
            if residual > max(8, int(count * 0.01)):
                failures.append(dict(card=c['s']['card'], frame=n, source_pixels=int(count),
                                     residual_pixels=residual))
    require(decoded == total == timing['frames'], 'Encoded frame count changed')
    result = dict(movie=movie, frames=total, unique_edge_frames_checked=len(wanted),
                  cards=[dict(card=c['s']['card'], frames_checked=c['checked'],
                              source_text_frames=c['lit'], worst_residual_pixels=c['worst_residual'],
                              worst_frame=c['worst_frame']) for c in checks], failures=failures,
                  encoded_sha256=report['sha256'], gameplay_verified=False)
    out = mt.VIEW / 'subtitle-timing-0.1.28' / (movie + '.encoded.json')
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(movie, len(checks), 'cards,', len(wanted), 'edge frames,', len(failures), 'failures', flush=True)
    require(not failures, 'Japanese fade remnants in ' + movie + '; see ' + str(out))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('movies', nargs='*')
    args = parser.parse_args()
    for name in args.movies or ['M1_MOVIE%03d' % i for i in range(1, 23)]:
        verify(name)
