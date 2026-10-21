"""Translated textures for the build: every texture whose original bytes match a spec'd texture
(work/translation/en/textures/*.json) is replaced by its relettered version, wherever it occurs."""
import hashlib
import json
import texture_text as tt
from ace_formats import require


class TextureText:
    def __init__(self, version=None):
        self.map = {}
        self.names = {}
        self.title_stamp = None
        specs = sorted(tt.SPEC.glob('*.json')) if tt.SPEC.exists() else []
        if not specs:
            return
        table = tt.by_name()
        for path in specs:
            if path.name.endswith('.en.json') and path.with_name(path.name[:-8] + '.json').exists():
                continue  # Prefer a local working spec; exports also work on a fresh checkout.
            spec = json.loads(path.read_text(encoding='utf-8'))
            if not any(l.get('en') for l in spec.get('labels', [])):
                continue
            require(spec['name'] in table, 'Unknown texture %s' % spec['name'])
            _, t = table[spec['name']]
            new, artwork = tt.apply_spec(t['data'], spec)
            if version and spec['name'] == 't3105.tm2':
                from title_stamp import stamp_texture
                new, self.title_stamp = stamp_texture(t['data'], artwork, version)
            require(len(new) == len(t['data']), 'Texture size changed: %s' % spec['name'])
            key = hashlib.sha1(t['data']).hexdigest()
            self.map[key] = new
            self.names[key] = spec['name']
        self.applied = {}

    def replace(self, data):
        key = hashlib.sha1(data).hexdigest()
        new = self.map.get(key)
        if new is not None:
            self.applied[self.names[key]] = self.applied.get(self.names[key], 0) + 1
        return new
