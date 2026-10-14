"""Find burned-in subtitles and title cards in a movie: per frame, the thin bright strokes in each row band; runs of
frames with text become candidate segments (with the frame of strongest text), written to
work/ui/movies/<movie>_subs.json, plus a crop sheet per movie for transcription.

    python tools/subtitle_scan.py M1_MOVIE001 [M1_MOVIE002 ...]
"""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw
import movie_text as mt

VIEW = mt.VIEW


def strokes(Y):
    th = Y - mt.box(Y, 3)
    return (th > 35) & (Y > 110)


def scan(movie):
    es, _ = mt.elementary(movie)
    total = len(mt.index(es)[1])
    rows = np.zeros((total, mt.H), np.float32)
    for n, buf in mt.frames(es, 0, total):
        Y = mt.planes(buf)[0]
        rows[n] = strokes(Y).sum(axis=1)
    return es, total, rows


def segments(rows, lo, hi, thresh=40, min_len=12, gap=4):
    e = rows[:, lo:hi].sum(axis=1)
    on = e > thresh
    out, n = [], 0
    while n < len(on):
        if on[n]:
            a = n
            quiet = 0
            while n < len(on) and quiet <= gap:
                quiet = 0 if on[n] else quiet + 1
                n += 1
            b = n - quiet
            if b - a >= min_len:
                peak = a + int(np.argmax(e[a:b]))
                out.append([a, b, peak, float(e[a:b].max())])
        else:
            n += 1
    return out


def main():
    for movie in sys.argv[1:]:
        es, total, rows = scan(movie)
        prof = rows.sum(axis=0)
        np.save(mt.CACHE / ('%s_rows.npy' % movie), rows)
        # text bands: rows with stroke energy, merged
        band = prof > prof.max() * 0.02
        bands, y = [], 0
        while y < mt.H:
            if band[y]:
                a = y
                while y < mt.H and band[y]:
                    y += 1
                if y - a >= 6:
                    bands.append([max(0, a - 4), min(mt.H, y + 4)])
            y += 1
        segs = []
        for lo, hi in bands:
            for a, b, peak, e in segments(rows, lo, hi):
                segs.append({'band': [lo, hi], 'frames': [a, b], 'peak': peak, 'energy': round(e)})
        segs.sort(key=lambda s: s['frames'][0])
        # crop sheet of every segment's peak frame (band only), numbered
        want = {s['peak'] for s in segs}
        crops = {}
        for n, buf in mt.frames(es, 0, total):
            if n in want:
                crops[n] = Image.frombytes('L', (mt.W, mt.H), buf[:mt.W * mt.H])
        tiles = []
        for i, s in enumerate(segs):
            lo, hi = s['band']
            t = crops[s['peak']].crop((0, lo, mt.W, hi)).resize((mt.W * 2, (hi - lo) * 2), Image.LANCZOS).convert('RGB')
            d = ImageDraw.Draw(t)
            d.text((2, 0), '#%d f%d-%d' % (i, s['frames'][0], s['frames'][1]), fill=(255, 255, 0))
            tiles.append(t)
        if tiles:
            W = mt.W * 2
            Hs = sum(t.height + 4 for t in tiles)
            sheet = Image.new('RGB', (W, Hs), (60, 0, 0))
            y = 0
            for t in tiles:
                sheet.paste(t, (0, y)); y += t.height + 4
            sheet.save(VIEW / ('%s_subs.png' % movie))
        (VIEW / ('%s_subs.json' % movie)).write_text(json.dumps({'movie': movie, 'frames': total, 'bands': bands,
                                                                  'segments': segs}, indent=1), encoding='utf-8')
        print(movie, total, 'frames; bands', bands, '; segments', len(segs))


if __name__ == '__main__':
    main()
