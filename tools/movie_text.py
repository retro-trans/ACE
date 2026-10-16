"""Burned-in Japanese in the FMV movies (MOVIE0/*.PSS, and MOVIE1/*.PSS named M1_MOVIENNN): erase it and scroll English in its place, then splice the
re-encoded GOPs into the original PSS byte for byte.

    python tools/movie_text.py analyze MOVIE001          # text block image, line bands -> work/ui/movies/
    python tools/movie_text.py preview MOVIE001 n [n..]  # before | after frames -> work/ui/movies/
    python tools/movie_text.py build MOVIE001            # -> work/output/movies/MOVIE001.PSS (+ .json)

Spec: work/translation/en/movies/<movie>.json, one entry per scrolling text segment:
    frames  [a, b]        display frames the text is on screen
    plate   [p0, p1]      frames whose per-pixel median is the clean background (a still), or "black"
    level   [x0,y0,x1,y1] untouched area used to follow background brightness (fades)
    speed, origin         text moves up `speed` px per frame; block row = screen row + speed * (n - origin)
    fade    [t0,t1,b1,b0] text alpha ramps 0->1 over rows t0..t1 and 1->0 over b1..b0
    colour  [Y, U, V]     lettering colour; shadow is a 1 px dark drop shadow
    lines   [{band: [y0, y1], align, x, ja, en}]  block rows of each Japanese line (erased) and its English;
            a line without "en" is erased only, and "keep": true leaves it untouched (already English).

The movie keeps every pack, audio packet and SCR. Only the GOPs that show text are re-encoded (same size, closed
GOPs, the stream's own inter matrix, padded with zero stuffing). Each new picture starts in its own video packet,
and the PTS/DTS of the packets in the changed range are rewritten for the pictures that now start there.
"""
import bisect
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from ace_formats import ROOT, SOURCE_ISO, iso_files, require
from lyrics import read_lyrics

SPEC = ROOT / 'work/translation/en/movies'
CACHE = ROOT / 'work/source/movies'       # elementary streams and analysis (git-ignored)
OUT = ROOT / 'work/output/movies'
VIEW = ROOT / 'work/ui/movies'
NOTO = r'C:\Windows\Fonts\NotoSansJP-VF.ttf'
W, H = 512, 448
FRAME = W * H * 3 // 2
TICKS = 3003                               # 90 kHz ticks per frame at 30000/1001
ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7,
          14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46,
          53, 60, 61, 54, 47, 55, 62, 63]


# ---------------------------------------------------------------- PSS container

def disc_path(name):
    """Spec name -> disc file: MOVIE001 is /MOVIE0/MOVIE001.PSS, M1_MOVIE001 is /MOVIE1/MOVIE001.PSS."""
    if name.startswith('M1_'):
        return '/MOVIE1/%s.PSS' % name[3:]
    return '/MOVIE0/%s.PSS' % name


def source_movie(name):
    """Copy the movie out of the source image (cached)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (name + '.PSS')
    with open(SOURCE_ISO, 'rb') as f:
        rec = iso_files(f)[disc_path(name)]
        if not path.exists() or path.stat().st_size != rec['size']:
            f.seek(rec['offset'])
            left = rec['size']
            with open(path, 'wb') as o:
                while left:
                    b = f.read(min(left, 8 << 20))
                    o.write(b)
                    left -= len(b)
    return path


def video_packets(path):
    """[(header offset, payload offset, payload length, ES offset)] of the video PES packets (stream 0xE0)."""
    out, es = [], 0
    with open(path, 'rb') as f:
        data = f.read()
    i = 0
    while i < len(data) - 4:
        if data[i:i + 4] == b'\0\0\1\xba':
            i += 14 + (data[i + 13] & 7)
            continue
        require(data[i:i + 3] == b'\0\0\1', 'PSS sync lost at %#x' % i)
        sid = data[i + 3]
        if sid == 0xb9:
            break
        length = struct.unpack_from('>H', data, i + 4)[0]
        if sid == 0xe0:
            p = i + 9 + data[i + 8]
            n = i + 6 + length - p
            out.append((i, p, n, es))
            es += n
        i += 6 + length
    del data
    return out


def elementary(name):
    """Write the video elementary stream of a movie to the cache; return (path, packets)."""
    pss = source_movie(name)
    packets = video_packets(pss)
    path = CACHE / (name + '.m2v')
    size = packets[-1][3] + packets[-1][2]
    if not path.exists() or path.stat().st_size != size:
        with open(pss, 'rb') as f, open(path, 'wb') as o:
            for _, p, n, _ in packets:
                f.seek(p)
                o.write(f.read(n))
    return path, packets


def start_codes(path, codes):
    """Offsets and following bytes of the start codes in ``codes`` (chunked scan)."""
    out = []
    with open(path, 'rb') as f:
        base, tail = 0, b''
        while True:
            chunk = f.read(32 << 20)
            if not chunk:
                break
            buf = tail + chunk
            start = base - len(tail)
            j = 0
            while True:
                j = buf.find(b'\0\0\1', j)
                if j < 0 or j + 8 > len(buf):
                    break
                if buf[j + 3] in codes:
                    out.append((start + j, buf[j + 3], buf[j + 4:j + 8]))
                j += 3
            tail = buf[max(0, len(buf) - 8) if j < 0 else j:]
            base += len(chunk)
    out = sorted(set(out))
    return out


def index(path):
    """GOPs [(es offset, first decode index, display base, picture count, header bytes)] and pictures
    [(es offset, decode index, display index, type)] of an elementary stream."""
    gops, pics = [], []
    for at, code, nxt in start_codes(path, (0xb8, 0x00)):
        if code == 0xb8:
            gops.append([at, len(pics), len(pics), 0, nxt])
        else:
            tr = (nxt[0] << 2) | (nxt[1] >> 6)
            kind = 'xIPB'[(nxt[1] >> 3) & 7]
            g = gops[-1]
            pics.append((at, len(pics), g[2] + tr, kind))
            g[3] += 1
    return [tuple(g) for g in gops], pics


def sequence_matrix(path):
    """Inter quantiser matrix of the sequence header, in raster order (ffmpeg's option order)."""
    with open(path, 'rb') as f:
        head = f.read(200)
    require(head[:4] == b'\0\0\1\xb3', 'ES does not start with a sequence header')
    bits = ''.join('{:08b}'.format(b) for b in head[4:])
    p = 12 + 12 + 4 + 4 + 18 + 1 + 10 + 1
    require(bits[p] == '0', 'Custom intra matrix not supported')
    p += 1
    require(bits[p] == '1', 'Expected a custom inter matrix')
    zz = [int(bits[p + 1 + 8 * k:p + 9 + 8 * k], 2) for k in range(64)]
    raster = [0] * 64
    for k, v in enumerate(zz):
        raster[ZIGZAG[k]] = v
    return raster


# ---------------------------------------------------------------- frames

def frames(path, a, b):
    """Yield (n, yuv420p bytes) for display frames a..b-1."""
    cmd = ['ffmpeg', '-v', 'error', '-i', str(path), '-vf', "select='between(n,%d,%d)'" % (a, b - 1),
           '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=FRAME * 2)
    n = a
    while n < b:
        buf = p.stdout.read(FRAME)
        if len(buf) < FRAME:
            break
        yield n, buf
        n += 1
    p.stdout.close()
    p.wait()
    require(n == b, 'Decoded %d frames, expected %d' % (n - a, b - a))


def planes(buf):
    f = np.frombuffer(buf, np.uint8)
    return (f[:W * H].reshape(H, W).astype(np.float32), f[W * H:W * H * 5 // 4].reshape(H // 2, W // 2).astype(np.float32),
            f[W * H * 5 // 4:].reshape(H // 2, W // 2).astype(np.float32))


def pack(Y, U, V):
    return b''.join(np.clip(np.round(p), 0, 255).astype(np.uint8).tobytes() for p in (Y, U, V))


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def box(a, r=1):
    out = np.zeros_like(a)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out += np.roll(np.roll(a, dy, 0), dx, 1)
    return out / (2 * r + 1) ** 2


class Segment:
    """One scrolling text segment: analysis (cached), erase and English overlay per frame."""

    def __init__(self, movie, es, k, spec):
        self.spec, self.es = spec, es
        self.a, self.b = spec['frames']
        self.v, self.origin = spec['speed'], spec['origin']
        self.local = spec.get('local', 0)    # radius of the per-pixel temporal median background (moving scenes)
        key = hashlib.sha1(json.dumps([spec['frames'], spec['plate'], spec['speed'], spec['origin'],
                                       spec.get('level')]).encode()).hexdigest()[:12]
        cache = CACHE / ('%s_%d_%s.npz' % (movie, k, key))
        self.rows = H + int(np.ceil(self.v * (self.b - self.origin))) + 8
        if cache.exists():
            z = np.load(cache)
            self.plate, self.pos, self.neg = (z['py'], z['pu'], z['pv']), z['pos'], z['neg']
        else:
            self._analyze()
            np.savez_compressed(cache, py=self.plate[0], pu=self.plate[1], pv=self.plate[2], pos=self.pos, neg=self.neg)
        self._masks()
        self._english()

    def offset(self, n):
        return self.v * (n - self.origin)

    def _analyze(self):
        if self.spec['plate'] == 'black':
            self.plate = (np.full((H, W), 16, np.float32), np.full((H // 2, W // 2), 128, np.float32),
                          np.full((H // 2, W // 2), 128, np.float32))
        else:
            p0, p1 = self.spec['plate']
            step = max(1, (p1 - p0) // 150)
            ys, us, vs = [], [], []
            for n, buf in frames(self.es, p0, p1):
                if (n - p0) % step == 0:
                    Y, U, V = planes(buf)
                    ys.append(Y), us.append(U), vs.append(V)
            self.plate = tuple(np.median(np.stack(x), axis=0).astype(np.float32) for x in (ys, us, vs))
        pos = np.zeros((self.rows, W), np.float32)
        neg = np.zeros((self.rows, W), np.float32)
        for n, buf in frames(self.es, self.a, self.b):
            if (n - self.a) % 2:
                continue
            Y = planes(buf)[0]
            d = Y - self.background(n, Y)[0]
            o = int(round(self.offset(n)))
            lo, hi = max(o, 0), min(o + H, self.rows)
            if lo < hi:
                pos[lo:hi] = np.maximum(pos[lo:hi], d[lo - o:hi - o])
                neg[lo:hi] = np.maximum(neg[lo:hi], -d[lo - o:hi - o])
        self.pos, self.neg = pos, neg

    def level(self, Y):
        if self.spec['plate'] == 'black':
            return 1.0
        x0, y0, x1, y1 = self.spec['level']
        p = self.plate[0][y0:y1, x0:x1] - 16
        y = Y[y0:y1, x0:x1] - 16
        ok = p > 8
        return float(np.median(y[ok] / p[ok])) if ok.any() else 1.0

    def background(self, n, Y):
        k = self.level(Y)
        return tuple(16 + (self.plate[0] - 16) * k for _ in (0,)) + tuple(128 + (p - 128) * k for p in self.plate[1:])

    def _masks(self):
        # Erase only inside each Japanese line's rows (and its x span, when given) and the segment's x region.
        area = np.zeros((self.rows, W), bool)
        for line in self.spec['lines']:
            if not line.get('keep'):
                y0, y1 = line['band']
                x0, x1 = line.get('span', [0, W])
                area[max(0, y0 - 3):y1 + 3, max(0, x0 - 4):x1 + 5] = True
        rx0, rx1 = self.spec.get('region', [0, W])
        area[:, :rx0] = False
        area[:, rx1:] = False
        m = ((self.pos > self.spec.get('erase_pos', 24)) | (self.neg > self.spec.get('erase_neg', 16))) & area
        self.mask = box(dilate(m, 2).astype(np.float32), 1)

    def _english(self):
        self.too_wide = []
        self.text, self.shadow = Segment.render_lines(self.spec, self.rows, self.too_wide)

    @staticmethod
    def render_lines(spec, rows, too_wide=None):
        """Text and shadow alpha for a block of ``rows`` rows; each line is drawn at 4x and reduced on its own."""
        s = 4
        faces = {}

        def face(size, weight):
            if (size, weight) not in faces:
                f = ImageFont.truetype(NOTO, size * s)
                try:
                    f.set_variation_by_axes([weight])
                except (OSError, AttributeError):
                    pass
                faces[size, weight] = f
            return faces[size, weight]
        text = np.zeros((rows, W), np.float32)
        too_wide = [] if too_wide is None else too_wide
        for line in spec['lines']:
            label = line.get('en')
            if not label or line.get('keep'):
                continue
            size = line.get('size', spec.get('size', 15))
            f = face(size, line.get('weight', spec.get('weight', 600)))
            y0, y1 = line['band']
            width = f.getlength(label)
            limit = line.get('width', spec.get('width', 368)) * s
            glyphs = Image.new('L', (int(width) + 8 * s, (size + 12) * s), 0)
            ImageDraw.Draw(glyphs).text((4 * s, glyphs.height // 2), label, font=f, fill=255, anchor='lm')
            scale = 1.0
            if width > limit:
                too_wide.append(label)
                scale = limit / width
                glyphs = glyphs.resize((int(glyphs.width * scale), glyphs.height), Image.LANCZOS)
            gw = width * scale
            x = line.get('x', 72) * s
            if line.get('align') == 'center':
                x -= gw / 2
            elif line.get('align') == 'right':
                x -= gw
            left = int(round((x - 4 * s * scale) / s))
            top = int(round(((y0 + y1) / 2 * s - glyphs.height // 2) / s))
            small = np.asarray(glyphs.resize((max(1, glyphs.width // s), max(1, glyphs.height // s)), Image.LANCZOS),
                               np.float32) / 255
            h, w = small.shape
            ya, yb, xa, xb = max(top, 0), min(top + h, rows), max(left, 0), min(left + w, W)
            if ya < yb and xa < xb:
                text[ya:yb, xa:xb] = np.maximum(text[ya:yb, xa:xb], small[ya - top:yb - top, xa - left:xb - left])
        blur = box(text, 1) * 0.5 + text * 0.5
        sh = np.zeros_like(text)
        sh[1:, 1:] = blur[:-1, :-1]
        return text, np.clip(sh * 1.4, 0, 1)

    def window(self, a, n):
        """Rows of block array ``a`` on screen at frame n (sub-pixel scroll)."""
        o = self.offset(n)
        i = int(np.floor(o))
        t = o - i
        pad = np.zeros((H + 1, W), np.float32)
        lo, hi = max(i, 0), min(i + H + 1, len(a))
        pad[lo - i:hi - i] = a[lo:hi]
        return pad[:H] * (1 - t) + pad[1:] * t

    def screen_mask(self, n):
        o = int(round(self.offset(n)))
        m = np.zeros((H, W), np.float32)
        lo, hi = max(o, 0), min(o + H, self.rows)
        if lo < hi:
            m[lo - o:hi - o] = self.mask[lo:hi]
        return m

    def local_background(self, n, m, ctx, by, bu, bv):
        """Per-pixel median of the neighbouring frames at times the text does not cover the pixel."""
        rows = np.where(m.any(axis=1))[0]
        if not len(rows):
            return by, bu, bv
        r0, r1 = rows[0] & ~1, min(H, (rows[-1] + 2) & ~1)
        ys, us, vs = [], [], []
        for k in sorted(ctx):
            if abs(k - n) > self.local:
                continue
            Yk, Uk, Vk = ctx[k]
            mk = self.screen_mask(k)[r0:r1] > 0.01 if self.a <= k < self.b else np.zeros((r1 - r0, W), bool)
            mkc = mk.reshape((r1 - r0) // 2, 2, W // 2, 2).any(axis=(1, 3))
            ys.append(np.where(mk, np.nan, Yk[r0:r1]))
            us.append(np.where(mkc, np.nan, Uk[r0 // 2:r1 // 2]))
            vs.append(np.where(mkc, np.nan, Vk[r0 // 2:r1 // 2]))
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            ly, lu, lv = (np.nanmedian(np.stack(x), axis=0) for x in (ys, us, vs))
        by, bu, bv = by.copy(), bu.copy(), bv.copy()
        by[r0:r1] = np.where(np.isnan(ly), by[r0:r1], ly)
        bu[r0 // 2:r1 // 2] = np.where(np.isnan(lu), bu[r0 // 2:r1 // 2], lu)
        bv[r0 // 2:r1 // 2] = np.where(np.isnan(lv), bv[r0 // 2:r1 // 2], lv)
        return by, bu, bv

    def apply(self, n, buf, ctx=None):
        if not self.a <= n < self.b:
            return buf
        Y, U, V = planes(buf)
        by, bu, bv = self.background(n, Y)
        m = self.screen_mask(n)
        if self.local and ctx:
            by, bu, bv = self.local_background(n, m, ctx, by, bu, bv)
        mc = m.reshape(H // 2, 2, W // 2, 2).max(axis=(1, 3))
        Y = Y * (1 - m) + by * m
        U = U * (1 - mc) + bu * mc
        V = V * (1 - mc) + bv * mc
        t0, t1, b1, b0 = self.spec['fade']
        rows = np.arange(H, dtype=np.float32)
        fade = (smooth((rows - t0) / max(1, t1 - t0)) * smooth((b0 - rows) / max(1, b0 - b1)))[:, None]
        a = self.window(self.text, n) * fade
        s = self.window(self.shadow, n) * fade * 0.75
        cy, cu, cv = self.spec.get('colour', [185, 127, 129])
        Y = Y * (1 - s) + 16 * s
        Y = Y * (1 - a) + cy * a
        ac = a.reshape(H // 2, 2, W // 2, 2).mean(axis=(1, 3))
        U = U * (1 - ac) + cu * ac
        V = V * (1 - ac) + cv * ac
        return pack(Y, U, V)


class StaticCard:
    """Japanese lettering that holds still over a still part of the picture (spec "type": "static"). The area
    around ``box`` is restored from the frames ``refs`` (just before and after the card, averaged), and English
    is drawn that fades in and out with the original lettering (its difference from that background)."""

    def __init__(self, movie, es, k, spec):
        self.spec, self.es = spec, es
        self.a, self.b = spec['frames']
        self.local = 0
        x0, y0, x1, y1 = spec['box']
        self.area = (slice(y0 - 6, y1 + 6), slice(x0 - 6, x1 + 6))
        self.area_c = (slice((y0 - 6) // 2, (y1 + 7) // 2), slice((x0 - 6) // 2, (x1 + 7) // 2))
        key = hashlib.sha1(json.dumps([spec['frames'], spec['box'], spec['refs'], spec.get('combine'),
                                       spec.get('ink_rows')]).encode()).hexdigest()[:12]
        cache = CACHE / ('%s_%d_%s.npz' % (movie, k, key))
        if cache.exists():
            z = np.load(cache)
            self.bg, self.energy, self.ink = (z['y'], z['u'], z['v']), z['e'], z['ink']
        else:
            refs = []
            for r in spec['refs']:
                if r == 'black':
                    refs.append((np.full((H, W), 16, np.float32), np.full((H // 2, W // 2), 128, np.float32),
                                 np.full((H // 2, W // 2), 128, np.float32)))
                    continue
                for n, buf in frames(es, r, r + 1):
                    refs.append(planes(buf))
            combine = np.min if spec.get('combine') == 'min' else np.mean
            self.bg = tuple(combine([p[i] for p in refs], axis=0).astype(np.float32) for i in range(3))
            # "ink_rows": restore only the lettering itself (pixels it ever covered on those rows, widened by
            # 2 px), so nothing outside it - such as the edge of the picture above a subtitle bar - is touched.
            rows = np.zeros(H, bool)
            for r0, r1 in spec.get('ink_rows') or []:
                rows[max(0, r0):min(H, r1)] = True
            ink = np.zeros((H, W), bool)
            e = []
            for n, buf in frames(es, self.a, self.b):
                Y = planes(buf)[0]
                e.append(float(np.abs(Y[self.area] - self.bg[0][self.area]).mean()))
                ink |= ((Y - self.bg[0]) > 20) & rows[:, None]
            ink[:, :x0 - 6] = False
            ink[:, x1 + 6:] = False
            self.energy = np.array(e, np.float32)
            self.ink = ink
            np.savez_compressed(cache, y=self.bg[0], u=self.bg[1], v=self.bg[2], e=self.energy, ink=self.ink)
        self.peak = float(np.percentile(self.energy, 90)) or 1.0
        self.too_wide = []
        self.text, self.shadow = Segment.render_lines(spec, H, self.too_wide)
        if spec.get('ink_rows'):
            feather = dilate(self.ink, 2).astype(np.float32)
        else:
            feather = np.zeros((H, W), np.float32)
            feather[self.area] = 1
        self.feather = np.clip(box(box(feather, 1), 1) * 1.0, 0, 1)
        self.feather_c = self.feather.reshape(H // 2, 2, W // 2, 2).mean(axis=(1, 3))

    def apply(self, n, buf, ctx=None):
        if not self.a <= n < self.b:
            return buf
        Y, U, V = planes(buf)
        f, fc = self.feather, self.feather_c
        Y = Y * (1 - f) + self.bg[0] * f
        U = U * (1 - fc) + self.bg[1] * fc
        V = V * (1 - fc) + self.bg[2] * fc
        alpha = min(1.0, self.energy[n - self.a] / self.peak)
        a = self.text * alpha
        sh = self.shadow * alpha * 0.75
        cy, cu, cv = self.spec.get('colour', [215, 128, 128])
        Y = Y * (1 - sh) + 16 * sh
        Y = Y * (1 - a) + cy * a
        ac = a.reshape(H // 2, 2, W // 2, 2).mean(axis=(1, 3))
        U = U * (1 - ac) + cu * ac
        V = V * (1 - ac) + cv * ac
        return pack(Y, U, V)


def _outline(alpha, r=1):
    """Alpha of a dark outline around ``alpha`` (r px), for text drawn over a moving picture."""
    return np.clip(box(dilate(alpha > 0.15, r).astype(np.float32), 1) * 1.2, 0, 1)


def _blend(Y, U, V, alpha, colour):
    cy, cu, cv = colour
    Y = Y * (1 - alpha) + cy * alpha
    ac = alpha.reshape(H // 2, 2, W // 2, 2).mean(axis=(1, 3))
    U = U * (1 - ac) + cu * ac
    V = V * (1 - ac) + cv * ac
    return Y, U, V


class Caption:
    """Text drawn over the picture without erasing anything (spec "type": "caption"): subtitles for speech or for
    Japanese left in place. ``lines`` as in render_lines; fades in and out over ``fade`` frames."""

    def __init__(self, movie, es, k, spec):
        self.spec = spec
        self.a, self.b = spec['frames']
        self.local = 0
        self.too_wide = []
        self.text, _ = Segment.render_lines(spec, H, self.too_wide)
        self.edge = _outline(self.text, spec.get('outline', 1))

    def alpha(self, n):
        f = self.spec.get('fade', 6)
        return min(1.0, (n - self.a + 1) / f, (self.b - n) / f)

    def apply(self, n, buf, ctx=None):
        if not self.a <= n < self.b:
            return buf
        k = max(0.0, self.alpha(n))
        Y, U, V = planes(buf)
        Y, U, V = _blend(Y, U, V, self.edge * k * 0.85, (16, 128, 128))
        Y, U, V = _blend(Y, U, V, self.text * k, self.spec.get('colour', [235, 128, 128]))
        return pack(Y, U, V)


def lyric_face(line):
    face = ImageFont.truetype(NOTO, line['size'] * 4)
    try:
        face.set_variation_by_axes([line.get('weight', 600)])
    except (OSError, AttributeError):
        pass
    return face


def lyric_wrap(text, line, width):
    """Word-wrapped source spans. No horizontal squeezing of lyric text."""
    import re
    face = lyric_face(line)
    spans, start, end = [], None, None
    for word in re.finditer(r'\S+', text):
        if start is not None and face.getlength(text[start:word.end()]) > width * 4:
            spans.append((start, end))
            start = None
        if start is None:
            start = word.start()
        end = word.end()
        require(face.getlength(text[start:end]) <= width * 4, 'A lyric word exceeds its available width')
    if start is not None:
        spans.append((start, end))
    return spans


def render_lyric(text, line, width, bottom):
    spans = lyric_wrap(text, line, width)
    height = line.get('line_height', line['size'] + 5)
    top = bottom - height * len(spans)
    require(top >= 0 and bottom <= H, 'Lyric block falls outside the frame')
    face = lyric_face(line)
    full = face.getlength(text) or 1.0
    lines, ranges = [], []
    for i, (a, b) in enumerate(spans):
        y0, y1 = top + i * height, top + (i + 1) * height
        label = text[a:b]
        lines.append(dict(line, en=label, band=[y0, y1], width=width))
        w = face.getlength(label) / 4
        x = line['x'] - w / 2
        require(x >= 0 and x + w <= W, 'Lyric line falls outside the frame')
        ranges.append((y0, y1, x, x+w, face.getlength(text[:a])/full, face.getlength(text[:b])/full))
    alpha, _ = Segment.render_lines({'lines': lines, 'width': width}, H)
    return alpha, ranges


class LyricsCaption(Caption):
    """A translation held across its sung phrases; only the lyric row index is in the spec."""

    def __init__(self, movie, es, k, spec):
        self.spec = spec
        self.a, self.b = spec['frames']
        self.local, self.too_wide = 0, []
        _, english = read_lyrics(ROOT / spec['lyrics'])[spec['index']]
        self.text, self.ranges = render_lyric(english or '', spec['line'], spec['width'], spec['bottom'])
        self.edge = _outline(self.text)


class Karaoke:
    """A sung line (spec "type": "karaoke"): the romaji line fills from left to right as it is sung (``knots``:
    [[frame, fraction of the line's width], ...]) and the translation line below stays still. The lyric text is
    read from the user's lyrics file (``lyrics`` path, line ``index``), never stored in the spec."""

    def __init__(self, movie, es, k, spec):
        self.spec = spec
        self.a, self.b = spec['frames']
        self.local = 0
        self.too_wide = []
        roma, english = read_lyrics(ROOT / spec['lyrics'])[spec['index']]
        rl = dict(spec['romaji_line'], en=roma)
        self.ranges = None
        if 'romaji_bottom' in spec:
            self.roma, self.ranges = render_lyric(roma, spec['romaji_line'], spec['width'], spec['romaji_bottom'])
        else:
            self.roma, _ = Segment.render_lines({'lines': [rl], 'width': spec.get('width', 470)}, H, self.too_wide)
        cols = np.where(self.roma.max(axis=0) > 0.05)[0]
        self.x0, self.x1 = (int(cols.min()), int(cols.max()) + 1) if len(cols) else (0, W)
        self.eng = np.zeros((H, W), np.float32)
        if spec.get('show_english', True) and english:
            el = dict(spec['english_line'], en=english)
            self.eng, _ = Segment.render_lines({'lines': [el], 'width': spec.get('width', 470)}, H, self.too_wide)
        self.edge_r = _outline(self.roma)
        self.edge_e = _outline(self.eng)
        self.cols = np.arange(W, dtype=np.float32)[None, :]
        self.backdrop = None
        if spec.get('backdrop'):
            d = spec['backdrop']
            rows = np.arange(H, dtype=np.float32)[:, None]
            a = smooth((rows-d['top'])/max(1,d.get('feather',8))) * (rows < d['bottom'])
            self.backdrop = np.broadcast_to(a*d.get('opacity',.86),(H,W)).copy()

    def progress(self, n):
        knots = self.spec['knots']
        fs = [k[0] for k in knots]
        return float(np.interp(n, fs, [k[1] for k in knots], left=0.0, right=1.0))

    def apply(self, n, buf, ctx=None):
        if not self.a <= n < self.b:
            return buf
        f = self.spec.get('fade', 6)
        k = max(0.0, min(1.0, (n - self.a + 1) / f, (self.b - n) / f))
        ke = k if self.spec.get('english_frames') is None else (
            1.0 if self.spec['english_frames'][0] <= n < self.spec['english_frames'][1] else 0.0) * k
        progress = self.progress(n)
        if self.ranges is None:
            fill = self.x0 + (self.x1 - self.x0) * progress
            sung = np.clip(fill - self.cols + 0.5, 0, 1)
        else:
            sung = np.zeros((H, W), np.float32)
            for y0, y1, x0, x1, p0, p1 in self.ranges:
                part = float(np.clip((progress-p0)/max(.000001,p1-p0),0,1))
                fill = x0 + (x1-x0)*part
                sung[y0:y1] = (1.0 if part >= 1 else 0.0 if part <= 0 else
                              np.clip(fill-self.cols+.5,0,1))
        Y, U, V = planes(buf)
        if self.backdrop is not None:
            Y, U, V = _blend(Y, U, V, self.backdrop * k, (16, 128, 128))
        Y, U, V = _blend(Y, U, V, np.maximum(self.edge_r * k, self.edge_e * ke) * 0.85, (16, 128, 128))
        Y, U, V = _blend(Y, U, V, self.roma * k * (1 - sung), self.spec.get('colour', [235, 128, 128]))
        Y, U, V = _blend(Y, U, V, self.roma * k * sung, self.spec.get('fill', [150, 70, 190]))
        Y, U, V = _blend(Y, U, V, self.eng * ke, self.spec.get('english_colour', [205, 135, 120]))
        return pack(Y, U, V)


# ---------------------------------------------------------------- spec, analysis and preview

LYRIC_TYPES = ('karaoke', 'lyrics_caption')   # segments that render song lyrics (user-supplied, never released)


def load(movie, no_lyrics=False):
    spec = json.loads((SPEC / (movie + '.json')).read_text(encoding='utf-8'))
    if no_lyrics:
        spec['segments'] = [s for s in spec['segments'] if s.get('type') not in LYRIC_TYPES]
    es, packets = elementary(movie)
    kinds = {'static': StaticCard, 'caption': Caption, 'karaoke': Karaoke, 'lyrics_caption': LyricsCaption}
    segs = [kinds.get(s.get('type'), Segment)(movie, es, k, s) for k, s in enumerate(spec['segments'])]
    return spec, es, packets, segs


def edited(es, segs, a, b, total):
    """Yield (n, original yuv, edited yuv) for display frames a..b-1, with the look-ahead the local backgrounds need."""
    k = max([s.local for s in segs] + [0])
    lo, hi = max(0, a - k), min(total, b + k)
    raw, ctx = {}, {}

    def emit(n):
        buf = raw[n]
        new = buf
        for s in segs:
            if s.a <= n < s.b:
                if s.local:
                    for j in range(n - s.local, n + s.local + 1):
                        if j in raw and j not in ctx:
                            ctx[j] = planes(raw[j])
                new = s.apply(n, new, ctx)
        return n, buf, new
    for n, buf in frames(es, lo, hi):
        raw[n] = buf
        done = n - k
        if a <= done < b:
            yield emit(done)
        for old in [j for j in raw if j < n - 2 * k - 1]:
            raw.pop(old)
            ctx.pop(old, None)
    for done in range(max(a, hi - k), b):
        yield emit(done)


def analyze(movie):
    spec, es, packets, segs = load(movie)
    VIEW.mkdir(parents=True, exist_ok=True)
    for k, s in enumerate(segs):
        if not isinstance(s, Segment):
            continue
        img = np.clip(s.pos * 2, 0, 255).astype(np.uint8)
        Image.fromarray(img).save(VIEW / ('%s_%d_block.png' % (movie, k)))
        m = s.pos > 40
        r = m.sum(1)
        y = 0
        while y < len(r):
            if r[y] > 3:
                y0 = y
                while y < len(r) and r[y] > 0:
                    y += 1
                cols = np.where(m[y0:y].any(0))[0]
                print('segment %d band [%d, %d] x %d..%d' % (k, y0, y, cols.min(), cols.max()))
            y += 1
        if s.too_wide:
            print('condensed to fit:', s.too_wide)


def preview(movie, ns):
    spec, es, packets, segs = load(movie)
    VIEW.mkdir(parents=True, exist_ok=True)
    total = len(index(es)[1])
    for want in ns:
        for n, buf, new in edited(es, segs, want, want + 1, total):
            pair = Image.new('RGB', (W * 2, H))
            for i, b in enumerate((buf, new)):
                img = Image.frombytes('L', (W, H), b[:W * H])
                u = Image.frombytes('L', (W // 2, H // 2), b[W * H:W * H * 5 // 4]).resize((W, H))
                v = Image.frombytes('L', (W // 2, H // 2), b[W * H * 5 // 4:]).resize((W, H))
                pair.paste(Image.merge('YCbCr', (img, u, v)).convert('RGB'), (i * W, 0))
            pair.save(VIEW / ('%s_%05d.png' % (movie, n)))
    print('previews in', VIEW)


# ---------------------------------------------------------------- encode and splice

def encode_gop(raw_frames, q, matrix):
    """Encode frames as one closed GOP; return the bytes from the GOP header to before the sequence end code."""
    n = len(raw_frames)
    cmd = ['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', '%dx%d' % (W, H), '-r', '30000/1001',
           '-i', '-', '-c:v', 'mpeg2video', '-g', str(n), '-bf', '2', '-flags', '+cgop', '-sc_threshold', '1000000000',
           '-qscale:v', str(q), '-qmin', '1', '-qmax', '28', '-non_linear_quant', '1', '-intra_vlc', '1', '-seq_disp_ext', '0',
           '-inter_matrix', ','.join(map(str, matrix)), '-f', 'mpeg2video', '-']
    out = subprocess.run(cmd, input=b''.join(raw_frames), stdout=subprocess.PIPE, check=True).stdout
    g = out.find(b'\0\0\1\xb8')
    e = out.rfind(b'\0\0\1\xb7')
    e = e if e > g else len(out)       # ffmpeg's raw output has no sequence end code
    require(g > 0 and out.count(b'\0\0\1\xb8') == 1, 'Unexpected encoder output')
    return out[g:e]


def pictures_of(gop):
    """[(offset in gop, temporal reference, type)] of the pictures in an encoded GOP."""
    out, j = [], 0
    while True:
        j = gop.find(b'\0\0\1\0', j)
        if j < 0:
            return out
        out.append((j, (gop[j + 4] << 2) | (gop[j + 5] >> 6), 'xIPB'[(gop[j + 5] >> 3) & 7]))
        j += 4


def layout(gop, start, end, pkt_starts, busy_before, next_busy):
    """Place an encoded GOP at ES offset ``start`` so that each picture starts in a packet of its own; pad with
    zeros to ``end``. Return the bytes or None when it does not fit."""
    pics = pictures_of(gop)
    out = bytearray(gop[:pics[0][0]])
    last = busy_before
    for k, (p, _, _) in enumerate(pics):
        q = pics[k + 1][0] if k + 1 < len(pics) else len(gop)
        at = start + len(out)
        pkt = bisect.bisect_right(pkt_starts, at) - 1
        if pkt <= last:
            pad = pkt_starts[last + 1] - at
            out += bytes(pad)
            pkt = last + 1
        last = pkt
        out += gop[p:q]
    if start + len(out) > end or last >= next_busy:
        return None
    return bytes(out) + bytes(end - start - len(out))


def ts_bytes(prefix, t):
    return bytes([(prefix << 4) | ((t >> 29) & 0x0e) | 1, (t >> 22) & 0xff, ((t >> 14) & 0xfe) | 1, (t >> 7) & 0xff,
                  ((t << 1) & 0xfe) | 1])


def build(movie, no_lyrics=False):
    tag = '.nolyrics' if no_lyrics else ''
    built_from = spec_hash(movie, no_lyrics)    # the spec this build reflects, even if it is edited meanwhile
    spec, es, packets, segs = load(movie, no_lyrics)
    pss = source_movie(movie)
    gops, pics = index(es)
    matrix = sequence_matrix(es)
    total = packets[-1][3] + packets[-1][2]
    pkt_starts = [p[3] for p in packets]
    pic_starts = [p[0] for p in pics]
    # Timing of the original stream: PTS = pts0 + display * TICKS, DTS = dts0 + decode * TICKS (anchors).
    with open(pss, 'rb') as f:
        def stamp(hdr):
            f.seek(hdr)
            h = f.read(19)
            flags = h[7] >> 6
            t = lambda b: ((b[0] >> 1) & 7) << 30 | b[1] << 22 | (b[2] >> 1) << 15 | b[3] << 7 | b[4] >> 1
            return flags, (t(h[9:14]) if flags & 2 else None), (t(h[14:19]) if flags == 3 else None)
        base = {}
        for hdr, _, n, at in packets[:400]:
            flags, pts, dts = stamp(hdr)
            k = bisect.bisect_left(pic_starts, at)
            if pts is not None and k < len(pics) and pic_starts[k] < at + n:
                base.setdefault('pts', set()).add(pts - pics[k][2] * TICKS)
                if dts is not None:
                    base.setdefault('dts', set()).add(dts - pics[k][1] * TICKS)
        require(len(base['pts']) == 1 and len(base['dts']) == 1, 'Irregular PTS/DTS in %s' % movie)
        pts0, dts0 = base['pts'].pop(), base['dts'].pop()
    # GOPs that show text.
    todo = []
    for g, (at, dec, disp, count, _) in enumerate(gops):
        if any(s.a < disp + count and disp < s.b for s in segs):
            todo.append(g)
    report = {'gops': len(todo), 'q': {}, 'bytes': 0}
    print(movie, 'encoding', len(todo), 'GOPs', flush=True)
    completed = 0
    new_es = CACHE / (movie + tag + '.new.m2v')
    new_pics = {}
    with open(es, 'rb') as src, open(new_es, 'wb') as dst:
        pos = 0
        runs = []
        for g in todo:
            if runs and runs[-1][1] == g - 1:
                runs[-1][1] = g
            else:
                runs.append([g, g])
        for g0, g1 in runs:
            first, last = gops[g0], gops[g1]
            a, b = first[2], last[2] + last[3]
            stream = edited(es, segs, a, b, len(pics))
            for g in range(g0, g1 + 1):
                at, dec, disp, count, head = gops[g]
                end = gops[g + 1][0] if g + 1 < len(gops) else total
                raw = []
                for _ in range(count):
                    n, _, new = next(stream)
                    raw.append(new)
                require(n == disp + count - 1, 'Frame order mismatch in GOP %d' % g)
                prev = bisect.bisect_left(pic_starts, at) - 1
                busy_before = bisect.bisect_right(pkt_starts, pics[prev][0]) - 1 if prev >= 0 else -1
                if g + 1 < len(gops):
                    nxt = pics[gops[g + 1][1]][0]
                    next_busy = bisect.bisect_right(pkt_starts, nxt) - 1
                else:
                    next_busy = len(packets)
                placed = None
                for q in range(2, 29):
                    gop = encode_gop(raw, q, matrix)
                    placed = layout(gop, at, end, pkt_starts, busy_before, next_busy)
                    if placed is not None:
                        break
                require(placed is not None, 'GOP %d does not fit' % g)
                # GOP header: original time code, closed GOP, no broken link.
                hdr = bytearray(placed[:8])
                hdr[4:8] = head
                hdr[7] = (hdr[7] | 0x40) & ~0x20
                placed = bytes(hdr) + placed[8:]
                got = pictures_of(placed)
                require(len(got) == count and sorted(t for _, t, _ in got) == list(range(count)), 'GOP %d pictures' % g)
                anchors = [t for _, t, k in got if k != 'B']
                require(max(anchors) == count - 1, 'GOP %d does not end on an anchor' % g)
                for i, (p, tr, kind) in enumerate(got):
                    new_pics[at + p] = (dec + i, disp + tr, kind)
                src.seek(pos)
                left = at - pos
                while left:
                    block = src.read(min(left, 8 << 20))
                    dst.write(block)
                    left -= len(block)
                dst.write(placed)
                pos = end
                report['q'][q] = report['q'].get(q, 0) + 1
                report['bytes'] += end - at
                completed += 1
                if completed % 50 == 0 or completed == len(todo):
                    print(movie, '%d/%d GOPs' % (completed, len(todo)), flush=True)
        src.seek(pos)
        while True:
            block = src.read(8 << 20)
            if not block:
                break
            dst.write(block)
    require(new_es.stat().st_size == total, 'New ES size differs')
    # Write the PSS: same packs; video payloads from the new ES; PES timestamps rewritten where pictures moved.
    changed = [(gops[g][0], gops[g + 1][0] if g + 1 < len(gops) else total) for g in todo]
    lo_list = [c[0] for c in changed]
    starts_all = sorted(new_pics)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / (movie + tag + '.PSS')
    with open(pss, 'rb') as src, open(new_es, 'rb') as nes, open(out, 'wb') as dst:
        pos = 0
        for hdr, p, n, at in packets:
            k = bisect.bisect_right(lo_list, at + n - 1) - 1
            touched = k >= 0 and changed[k][0] < at + n and at < changed[k][1]
            if not touched:
                continue
            src.seek(pos)
            dst.write(src.read(hdr - pos))
            src.seek(hdr)
            head = bytearray(src.read(p - hdr))
            # Header data is normally exactly PTS+DTS (10 bytes). A longer one (the stream's first packet adds 3
            # bytes of PES extension) can only be rewritten in place, with the same timestamp layout.
            fixed = head[8] != 10
            nes.seek(at)
            payload = nes.read(n)
            j = bisect.bisect_left(starts_all, at)
            pic = new_pics[starts_all[j]] if j < len(starts_all) and starts_all[j] < at + n else None
            if pic is None:
                # A picture of the untouched stream may start here (packet straddling the range edge).
                i = bisect.bisect_left(pic_starts, at)
                if i < len(pics) and pic_starts[i] < at + n and not any(c[0] <= pic_starts[i] < c[1] for c in changed):
                    pic = (pics[i][1], pics[i][2], pics[i][3])
            if fixed:
                old = head[7] >> 6
                want = 0 if pic is None else (2 if pic[2] == 'B' else 3)
                require(old == want, 'Cannot change the timestamps of a %d-byte PES header' % head[8])
                if pic is not None:
                    dec, disp, kind = pic
                    head[9:14] = ts_bytes(want, pts0 + disp * TICKS)
                    if want == 3:
                        head[14:19] = ts_bytes(1, dts0 + dec * TICKS)
            elif pic is None:
                head[7] &= 0x3f
                head[9:19] = b'\xff' * 10
            else:
                dec, disp, kind = pic
                pts = pts0 + disp * TICKS
                if kind == 'B':
                    head[7] = (head[7] & 0x3f) | 0x80
                    head[9:19] = ts_bytes(2, pts) + b'\xff' * 5
                else:
                    head[7] = (head[7] & 0x3f) | 0xc0
                    head[9:19] = ts_bytes(3, pts) + ts_bytes(1, dts0 + dec * TICKS)
            dst.write(head)
            dst.write(payload)
            pos = p + n
        src.seek(pos)
        while True:
            block = src.read(8 << 20)
            if not block:
                break
            dst.write(block)
    require(out.stat().st_size == pss.stat().st_size, 'PSS size changed')
    # Verify: the rebuilt PSS carries the new ES, and the stream decodes to the full frame count.
    check = video_packets(out)
    require([(p[2], p[3]) for p in check] == [(p[2], p[3]) for p in packets], 'Packet layout changed')
    h = hashlib.sha1()
    with open(out, 'rb') as f:
        for _, p, n, _ in check:
            f.seek(p)
            h.update(f.read(n))
    h2 = hashlib.sha1()
    with open(new_es, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h2.update(block)
    require(h.hexdigest() == h2.hexdigest(), 'PSS video differs from the new ES')
    count = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                            'stream=nb_read_frames', '-of', 'csv=p=0', str(out)], stdout=subprocess.PIPE, check=True)
    report['frames'] = int(count.stdout.strip().split(b',')[0])
    require(report['frames'] == len(pics), 'Frame count %d, expected %d' % (report['frames'], len(pics)))
    report['spec'] = built_from
    report['sha256'] = sha256(out)
    (OUT / (movie + tag + '.json')).write_text(json.dumps(report, indent=1), encoding='utf-8')
    print(movie, report)
    return report


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def spec_hash(movie, no_lyrics=False):
    raw = (SPEC / (movie + '.json')).read_bytes()
    digest = hashlib.sha1(raw)
    if no_lyrics:
        return hashlib.sha1(raw + b'|nolyrics').hexdigest()     # the lyrics file is not used
    paths = sorted({s['lyrics'] for s in json.loads(raw)['segments'] if 'lyrics' in s})
    for path in paths:
        digest.update(path.encode('utf-8'))
        digest.update((ROOT / path).read_bytes())
    return digest.hexdigest()


def ready(only=None, no_lyrics=False):
    """{disc path: built path} for every movie spec (or the movies in ``only``); fails when a build is missing or
    stale. With ``no_lyrics`` (public releases) the builds without song lyrics are used, and a movie whose only
    edits are lyrics stays original."""
    out = {}
    for path in sorted(SPEC.glob('*.json')) if SPEC.exists() else []:
        if path.name.endswith('.en.json'):
            continue
        movie = path.stem
        if only is not None and movie not in only:
            continue
        segments = json.loads(path.read_text(encoding='utf-8'))['segments']
        has_lyrics = any(s.get('type') in LYRIC_TYPES for s in segments)
        if no_lyrics and not [s for s in segments if s.get('type') not in LYRIC_TYPES]:
            continue                                  # only lyrics: the movie stays original
        no_lyrics_here = no_lyrics and has_lyrics     # a movie without lyrics uses its normal build
        tag = '.nolyrics' if no_lyrics_here else ''
        rep = OUT / (movie + tag + '.json')
        require(rep.exists() and json.loads(rep.read_text(encoding='utf-8'))['spec'] == spec_hash(movie, no_lyrics_here),
                'Movie %s is not built for its current spec: run tools/movie_text.py build %s%s'
                % (movie, movie, ' --no-lyrics' if no_lyrics_here else ''))
        out[disc_path(movie)] = OUT / (movie + tag + '.PSS')
    return out


if __name__ == '__main__':
    cmd, movie = sys.argv[1], sys.argv[2]
    if cmd == 'analyze':
        analyze(movie)
    elif cmd == 'preview':
        preview(movie, [int(x) for x in sys.argv[3:]])
    elif cmd == 'build':
        build(movie, '--no-lyrics' in sys.argv)
