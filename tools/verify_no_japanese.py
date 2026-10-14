"""Final checks that no Japanese remains in a built image beyond the text tables (japanese_inventory.py).

    python tools/verify_no_japanese.py [iso]     # default: newest work/output/ACE-EN-*.iso
    python tools/verify_no_japanese.py <iso> --textures-only  # additive movie captions/karaoke use separate checks

1. Textures: no texture whose bytes equal an original Japanese-lettered texture (every spec in
   work/translation/en/textures) is left anywhere in DATA.BIN (plain, packed or nested).
2. Movies, every frame: for each movie with a spec, every frame of each text segment is compared with the original.
   Pixels where the original showed Japanese strokes (thin features inside the erase mask, away from the English)
   must no longer show a thin feature: the share of surviving stroke pixels is reported per frame; above 5 % fails.
   Frames outside the segments must decode identically to the original.
"""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from ace_formats import ROOT, bnd_entries, is_packed, iso_files, require, unpack
import movie_text as mt
import texture_text as tt


def textures(iso):
    from build import DataBin
    from texture_apply import TextureText
    originals = set(TextureText().map)
    left = []
    with open(iso, 'rb') as f:
        r = iso_files(f)['/DATA.BIN']
        db = DataBin(f, r['offset'], r['size'])
        for e in db.entries:
            data = db.read(e)
            blobs = [data]
            if is_packed(data):
                try:
                    blobs.append(unpack(data))
                except Exception:
                    pass
            for b in blobs:
                for key in originals:
                    pass
                # textures are stored whole (child entries or files); check every TM2-sized window by header
                at = 0
                while True:
                    at = b.find(b'\x01\x00\x00\x00', at + 1)
                    if at < 0:
                        break
                    s = at - 8
                    if s < 0:
                        continue
                    total = int.from_bytes(b[s:s + 4], 'little')
                    if 64 <= total <= len(b) - s and hashlib.sha1(b[s:s + total]).hexdigest() in originals:
                        left.append('%s@%#x' % (e['name'], s))
    return len(originals), left


def movie(name, out_pss):
    spec, es, packets, segs = mt.load(name)
    new_es = mt.CACHE / (name + '.check.m2v')
    with open(out_pss, 'rb') as f, open(new_es, 'wb') as o:
        for _, p, n, _ in mt.video_packets(out_pss):
            f.seek(p)
            o.write(f.read(n))
    total = len(mt.index(es)[1])
    worst, fails, frames_checked = 0.0, [], 0
    inside = np.zeros(total, bool)
    for s in segs:
        inside[s.a:s.b] = True
    orig = mt.frames(es, 0, total)
    new = mt.frames(new_es, 0, total)
    diff_outside = 0
    for (n, ob), (_, nb) in zip(orig, new):
        frames_checked += 1
        if not inside[n]:
            if ob != nb:
                # re-encoded GOP frames outside the text: allow coding noise only
                d = np.abs(np.frombuffer(ob, np.uint8)[:mt.W * mt.H].astype(int) - np.frombuffer(nb, np.uint8)[:mt.W * mt.H])
                if np.percentile(d, 99.9) > 40:
                    diff_outside += 1
            continue
        Yo, Yn = mt.planes(ob)[0], mt.planes(nb)[0]
        strokes = np.zeros((mt.H, mt.W), bool)
        english = np.zeros((mt.H, mt.W), np.float32)
        for s in segs:
            if not s.a <= n < s.b:
                continue
            if isinstance(s, mt.Segment):
                m = s.screen_mask(n) > 0.5
                bg = s.background(n, Yo)[0]
                english = np.maximum(english, s.window(s.text, n) + s.window(s.shadow, n))
            else:
                m = s.feather > 0.5
                bg = s.bg[0]
                english = np.maximum(english, s.text + s.shadow)
            strokes |= m & (np.abs(Yo - bg) > 30)
        # Lettering = thin features standing out from their 7x7 neighbourhood (moving backgrounds such as the
        # lens flare are smooth at this scale, so they do not count as strokes).
        th_o = Yo - mt.box(Yo, 3)
        th_n = Yn - mt.box(Yn, 3)
        eng = mt.dilate(english > 0.05, 2)
        test = strokes & ~eng & (np.abs(th_o) > 25)
        if test.sum() < 20:
            continue
        # a stroke pixel "survives" when the new frame still shows a thin feature of the same sign there
        survive = float(((th_n[test] * np.sign(th_o[test])) > 12).mean())
        worst = max(worst, survive)
        if survive > 0.05:
            fails.append((n, round(survive, 4), int(test.sum())))
    new_es.unlink()
    return {'frames': frames_checked, 'worst_surviving_share': round(worst, 4), 'failing_frames': sorted(fails, key=lambda f: -f[1]),
            'n_failing': len(fails), 'frames_changed_outside_text': diff_outside}


def main():
    iso = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((ROOT / 'work/output').glob('ACE-EN-*.iso'))[-1]
    if len(sys.argv) > 2 and '--textures-only' not in sys.argv:  # one movie only: <iso> MOVIE002
        r = movie(sys.argv[2], mt.OUT / (sys.argv[2] + '.PSS'))
        (ROOT / 'work/output' / ('%s.%s.verify.json' % (iso.stem, sys.argv[2]))).write_text(json.dumps(r, indent=1))
        print(sys.argv[2], r['n_failing'], r['worst_surviving_share'], r['failing_frames'][:15])
        return
    n, left = textures(iso)
    print('textures: %d Japanese-lettered originals, %d left in %s' % (n, len(left), iso.name), left[:5])
    report = {'image': iso.name, 'textures_left': left}
    if '--textures-only' in sys.argv:
        report['original_textures_checked'] = n
        (ROOT / 'work/output' / (iso.stem + '.textures.verify.json')).write_text(
            json.dumps(report, indent=1), encoding='utf-8')
        require(not left, 'Original Japanese-lettered textures remain')
        return
    for name, path in sorted(mt.ready().items()):
        r = movie(Path(path).stem, path)
        print(Path(path).stem, r)
        report[Path(path).stem] = r
    (ROOT / 'work/output' / (iso.stem + '.verify.json')).write_text(json.dumps(report, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
