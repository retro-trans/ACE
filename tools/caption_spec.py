"""Subtitles drawn over a movie without erasing anything: speech (timed with tools/whisper_tool.py) or Japanese
text left in place.

    python tools/caption_spec.py MOVIE001

Reads work/translation/en/movies/captions/<movie>.json: {"movie", "rows": [{"start", "end" (seconds) or
"frames": [a, b], "ja", "en"}], optional "y" (bottom edge of the text, default 444), "size"}. Replaces the caption
segments of work/translation/en/movies/<movie>.json, keeping its other segments.
"""
import json
import sys
from PIL import ImageFont
import movie_text as mt

FPS = 30000 / 1001


def wrap(text, size, weight, width):
    f = mt.ImageFont.truetype(mt.NOTO, size * 4)
    try:
        f.set_variation_by_axes([weight])
    except (OSError, AttributeError):
        pass
    if '\n' in text:
        return text.split('\n')
    if f.getlength(text) <= width * 4:
        return [text]
    words = text.split(' ')
    best = min(range(1, len(words)), key=lambda k: max(f.getlength(' '.join(words[:k])), f.getlength(' '.join(words[k:]))))
    return [' '.join(words[:best]), ' '.join(words[best:])]


def build(movie):
    src = json.loads((mt.SPEC / 'captions' / ('%s.json' % movie)).read_text(encoding='utf-8'))
    size, weight, width = src.get('size', 15), src.get('weight', 650), src.get('width', 470)
    bottom, pitch = src.get('y', 444), size + 7
    segments = []
    for r in src['rows']:
        if not r.get('en'):
            continue
        a, b = r['frames'] if 'frames' in r else (round(r['start'] * FPS), round(r['end'] * FPS) + 8)
        lines = wrap(r['en'], size, weight, width)
        top = bottom - pitch * len(lines)
        segments.append({'type': 'caption', 'frames': [a, b], 'ja': r.get('ja', ''), 'fade': 6,
                         'outline': src.get('outline', 1),
                         'lines': [{'band': [top + pitch * i, top + pitch * (i + 1)], 'en': t, 'align': 'center',
                                    'x': 256, 'width': width, 'size': size, 'weight': weight}
                                   for i, t in enumerate(lines)]})
    path = mt.SPEC / ('%s.json' % movie)
    spec = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'movie': movie, 'segments': []}
    spec['segments'] = [s for s in spec['segments'] if s.get('type') != 'caption'] + segments
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding='utf-8')
    print(movie, len(segments), 'captions')


if __name__ == '__main__':
    for m in sys.argv[1:]:
        build(m)
