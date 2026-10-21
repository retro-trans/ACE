"""Check a story-restoration build against 0.1.23; --write saves the comparison report.

Use verify_movie_scope.py separately to verify all on-disc movies and their soundtracks.
"""
import argparse
import json
from pathlib import Path

from ace_formats import ROOT, SOURCE_ISO, iso_files, require
from texture_text import SPEC, apply_spec
from title_stamp import TEXTURE, stamp_texture
from verify_title_stamp import database, leaf, children
from verify_movie_scope import range_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    current = json.loads(args.iso.with_suffix('.json').read_text(encoding='utf-8'))
    prior_path = ROOT / 'work/output/ACE-EN-0.1.23.iso'
    prior = json.loads(prior_path.with_suffix('.json').read_text(encoding='utf-8'))
    require(not current['movies_without_lyrics'], 'Lyrics must be included')
    for name, digest in prior['movies'].items():
        require(current['movies'].get(name) == digest, 'Opening/ending movie changed: ' + name)
    with open(SOURCE_ISO, 'rb') as source:
        db = database(source)
        original = db.read(next(e for e in db.entries if leaf(e['name']) == TEXTURE))
    spec = json.loads((SPEC / 't3105_tm2.json').read_text(encoding='utf-8'))
    _, artwork = apply_spec(original, spec)
    title, stamp = stamp_texture(original, artwork, current['version'])
    require(current['title_stamp'] == stamp, 'Incorrect title version')
    changed, other_files = [], []
    with prior_path.open('rb') as old, args.iso.open('rb') as new:
        a, b = database(old), database(new)
        require([e['name'] for e in a.entries] == [e['name'] for e in b.entries], 'Resource list changed')
        for ae, be in zip(a.entries, b.entries):
            aa, bb = a.read(ae), b.read(be)
            if aa == bb:
                continue
            name = leaf(ae['name'])
            changed.append(ae['name'])
            if name == TEXTURE:
                require(bb == title, 'Incorrect title texture')
            else:
                require(name in ('MenuTitle.csc', 'MenuTitleIntro.csc'), 'Unrelated resource changed: ' + name)
                ac, bc = children(aa), children(bb)
                require(ac.keys() == bc.keys(), 'Title bundle children changed')
                for key in ac:
                    require(bc[key] == (title if leaf(key) == TEXTURE else ac[key]),
                            'Unrelated title bundle content changed: ' + key)
        require(len(changed) == 3, 'Expected exactly three updated title texture copies')
        af, bf = iso_files(old), iso_files(new)
        require(af.keys() == bf.keys(), 'Disc file list changed')
        for name, entry in af.items():
            if name == '/DATA.BIN' or name.endswith('.PSS'):
                continue
            other = bf[name]
            require(entry['size'] == other['size'], 'File size changed: ' + name)
            require(range_hash(old, entry['offset'], entry['size']) ==
                    range_hash(new, other['offset'], other['size']), 'Unrelated disc file changed: ' + name)
            other_files.append(name)
    result = dict(iso=args.iso.name, baseline=prior_path.name, changed_resources=changed,
                  other_game_data_unchanged=True, hud_font_unchanged=True, lyrics_movies_unchanged=True,
                  unchanged_disc_files=other_files, runtime_verified=False)
    print(json.dumps(result, indent=1))
    if args.write:
        args.iso.with_suffix('.restore.verify.json').write_text(json.dumps(result, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
