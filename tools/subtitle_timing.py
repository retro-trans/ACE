"""Refine story-card ranges through their faint fades on the black caption panel.

The original scan detects bright strokes (Y > 110), which omits visible fade frames.
This pass follows low-contrast lettering (Y > 20 on limited-range black Y=16) on
the known text rows, with a two-frame guard. It updates both source cards and their
generated specs. Dry run by default. Only black-background static cards are supported.
"""
import argparse
import json
import numpy as np
import movie_text as mt
from ace_formats import require

MARGIN = 40
GUARD = 2


def refine(movie, write=False):
    path = mt.SPEC / (movie + '.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    cards_path = mt.SPEC / 'subs' / (movie + '.json')
    cards = json.loads(cards_path.read_text(encoding='utf-8'))
    card_map = {c['id']: c for c in cards['cards']}
    es, _ = mt.elementary(movie)
    total = len(mt.index(es)[1])
    pending = []
    for s in data['segments']:
        require(s.get('type') == 'static' and s.get('refs') == ['black'],
                'Timing refinement requires static lettering on black')
        a, b = s.get('scan_frames', s['frames'])
        lo, hi = max(0, a - MARGIN), min(total, b + MARGIN)
        rows = np.zeros(mt.H, bool)
        for r0, r1 in s['ink_rows']:
            rows[max(0, r0):min(mt.H, r1)] = True
        pending.append(dict(segment=s, a=a, b=b, lo=lo, hi=hi, rows=rows,
                            counts=np.zeros(hi - lo, np.int32)))
    peaks = {card_map[p['segment']['card']]['peak'] for p in pending}
    peak_frames = {}
    for n, buf in mt.frames(es, 0, max(peaks) + 1):
        if n in peaks:
            peak_frames[n] = np.frombuffer(buf, np.uint8, mt.W * mt.H).reshape(mt.H, mt.W).copy()
    for p in pending:
        s = p['segment']
        mask = (peak_frames[card_map[s['card']]['peak']] > 80) & p['rows'][:, None]
        mask[:, :s['box'][0]] = False
        mask[:, s['box'][2]:] = False
        p['mask'] = mask
    for p in pending:
        # Adjacent one-line and two-line cards can share rows during a crossfade.
        # Track pixels unique to this card, so the next card does not extend it.
        mask = p['mask'].copy()
        for q in pending:
            if q is not p and p['lo'] < q['hi'] and q['lo'] < p['hi']:
                mask &= ~mt.dilate(q['mask'], 1)
        require(np.count_nonzero(mask) >= 100, 'Insufficient unique text pixels: ' + movie)
        p['tracking_mask'] = mask
    for n, buf in mt.frames(es, 0, total):
        active = [p for p in pending if p['lo'] <= n < p['hi']]
        if not active:
            continue
        y = np.frombuffer(buf, np.uint8, mt.W * mt.H).reshape(mt.H, mt.W)
        for p in active:
            p['counts'][n - p['lo']] = np.count_nonzero(y[p['tracking_mask']] > 20)
    changes = []
    for p in pending:
        s, a, b, lo, hi = (p[k] for k in ('segment', 'a', 'b', 'lo', 'hi'))
        on = p['counts'] >= 24
        first, end = a, b
        while first > lo and on[first - lo - 1]:
            first -= 1
        while end < hi and on[end - lo]:
            end += 1
        require(first > lo or lo == 0, 'Fade exceeds scan margin at start: ' + movie)
        require(end < hi or hi == total, 'Fade exceeds scan margin at end: ' + movie)
        start, stop = max(0, first - GUARD), min(total, end + GUARD)
        changes.append(dict(card=s['card'], scan_frames=[a, b], visible_frames=[first, end],
                            frames=[start, stop], leading_frames=a - first, trailing_frames=end - b))
        s['scan_frames'] = [a, b]
        s['frames'] = [start, stop]
        s['timing_revision'] = 'faint-fades-v1'
        s['fade_measure'] = 'ink_rows'
        card_map[s['card']]['frames'] = [start, stop]
        card_map[s['card']]['scan_frames'] = [a, b]
        card_map[s['card']]['timing_revision'] = 'faint-fades-v1'
        card_map[s['card']]['fade_measure'] = 'ink_rows'
    # A title can be manually appended after the subtitles. Compare in timeline
    # order, and share a short blank gap rather than overlapping two erase masks.
    ordered = sorted(changes, key=lambda c: c['frames'][0])
    for left, right in zip(ordered, ordered[1:]):
        require(left['visible_frames'][1] <= right['visible_frames'][0],
                'Visible card ranges overlap: ' + movie)
        if left['frames'][1] > right['frames'][0]:
            boundary = (left['visible_frames'][1] + right['visible_frames'][0]) // 2
            left['frames'][1] = right['frames'][0] = boundary
    by_card = {c['card']: c for c in changes}
    for s in data['segments']:
        s['frames'] = by_card[s['card']]['frames']
        card_map[s['card']]['frames'] = list(s['frames'])
    report = dict(movie=movie, frames=total, cards=changes, threshold_y=20,
                  minimum_pixels=24, guard_frames=GUARD)
    if write:
        for output, value in ((path, data), (cards_path, cards)):
            output.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding='utf-8')
        out = mt.VIEW / 'subtitle-timing-0.1.28'
        out.mkdir(parents=True, exist_ok=True)
        (out / (movie + '.json')).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(movie, len(changes), 'cards;', 'leading', sorted({c['leading_frames'] for c in changes}),
          'trailing', sorted({c['trailing_frames'] for c in changes}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('movies', nargs='*')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    names = args.movies or ['M1_MOVIE%03d' % i for i in range(1, 23)]
    for name in names:
        refine(name, args.write)
