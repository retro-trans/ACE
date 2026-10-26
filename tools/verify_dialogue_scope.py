"""Compare 0.1.32 to 0.1.31: one capacity instruction and three title stamps."""
import hashlib
import json

from ace_formats import ROOT, iso_files, require
from dialogue_buffer import patch
from verify_hud_warning import database
from verify_shared_fonts import named, leaf


def digest(f, record):
    f.seek(record['offset'])
    h, remaining = hashlib.sha256(), record['size']
    while remaining:
        chunk = f.read(min(8 << 20, remaining))
        require(bool(chunk), 'Truncated disc file')
        h.update(chunk)
        remaining -= len(chunk)
    return h.hexdigest()


def main():
    base = ROOT / 'work/output/ACE-EN-0.1.31.iso'
    target = ROOT / 'work/output/ACE-EN-0.1.32.iso'
    changes, movies = [], {}
    with base.open('rb') as a, target.open('rb') as b:
        da, db = database(a), database(b)
        require([e['name'] for e in da.entries] == [e['name'] for e in db.entries],
                'Resource inventory changed')
        for ea, eb in zip(da.entries, db.entries):
            aa, bb = da.read(ea), db.read(eb)
            if aa == bb:
                continue
            name = leaf(ea['name'])
            changes.append(ea['name'])
            if name == 't3105.tm2':
                continue
            require(name in ('MenuTitle.csc', 'MenuTitleIntro.csc'),
                    'Unrelated resource changed: ' + ea['name'])
            ac, bc = named(aa), named(bb)
            require(ac.keys() == bc.keys(), 'Title bundle inventory changed')
            require([leaf(k) for k in ac if ac[k] != bc[k]] == ['t3105.tm2'],
                    'Unrelated title bundle child changed')
        require(len(changes) == 3, 'Unexpected title copy count')
        fa, fb = iso_files(a), iso_files(b)
        require(fa.keys() == fb.keys(), 'Disc inventory changed')
        for name in fa:
            if name == '/DATA.BIN':
                continue
            if name == '/SLPS_253.94':
                a.seek(fa[name]['offset']); b.seek(fb[name]['offset'])
                expected = bytearray(a.read(fa[name]['size']))
                patch(expected, {})
                require(expected == b.read(fb[name]['size']), 'Unrelated executable change')
            else:
                ha, hb = digest(a, fa[name]), digest(b, fb[name])
                require(ha == hb, 'Unrelated disc-file difference: ' + name)
                if name.endswith('.PSS'):
                    movies[name] = hb
    ar = json.loads(base.with_suffix('.json').read_text(encoding='utf-8'))
    br = json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
    require(ar['movies'] == br['movies'] and not br['movies_without_lyrics'],
            'Movie/lyric manifest changed')
    result = dict(baseline=str(base), target=str(target), changed_resources=changes,
                  executable_changes=['0x2018dc'], font_bytes_identical=True,
                  mission_resources_identical=True, movies_and_lyrics_unchanged=True,
                  all_on_disc_movie_hashes=movies, runtime_verified=False)
    out = ROOT / 'work/ui/dialogue-buffer-0.1.32/scope-verification.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS: one capacity instruction, three title stamps; all other resources/files identical')


if __name__ == '__main__':
    main()
