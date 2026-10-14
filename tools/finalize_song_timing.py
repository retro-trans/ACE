"""Assemble the best supported alignment windows for the supplied songs, without storing lyrics."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'work/source/movies'


def main():
    for movie in ('MOVIE003', 'MOVIE002'):
        target = CACHE / (movie + '.lyrics_timing.json')
        base = json.loads(target.read_text(encoding='utf-8'))
        if movie == 'MOVIE003':
            choices = [('MOVIE003.full_alignment.json', list(range(15)) + list(range(33,38))),
                       ('MOVIE003.lyrics_timing.json', list(range(15,25))),
                       ('MOVIE003.align_b.json', [25])]
            omitted = list(range(26,33))
        else:
            choices = [('MOVIE002.lyrics_timing.json', [i for i in range(21) if i not in (16,17)]),
                       ('MOVIE002.align_bridge.json', [16,17])]
            omitted = []
        rows = {}
        for source, indices in choices:
            data = json.loads((CACHE/source).read_text(encoding='utf-8'))
            assert data['lyrics_sha256'] == base['lyrics_sha256']
            by_id = {r['row']: r for r in data['rows']}
            for i in indices:
                row = dict(by_id[i], alignment_source=source)
                assert 'start' in row and row['matched']/row['letters'] >= .5, (movie,i)
                rows[i] = row
        ordered = [rows[k] for k in sorted(rows)]
        assert all(a['start'] < b['start'] for a,b in zip(ordered,ordered[1:]))
        lyric_file = ROOT/'work/translation/en/movies/lyrics'/(movie+'.txt')
        assert hashlib.sha256(lyric_file.read_bytes()).hexdigest() == base['lyrics_sha256']
        base['rows'] = sorted(ordered+[{'row':i,'reason':'omitted in the movie arrangement'} for i in omitted],
                              key=lambda r:r['row'])
        base['alignment_windows'] = [s for s,_ in choices]
        base.pop('window', None)  # This result combines several windows, not just the base input's crop.
        base['sung_range'] = [ordered[0]['start'], ordered[-1]['end']]
        base['review'] = 'Numerical alignment and phrase coverage checked; final listening review remains.'
        target.write_text(json.dumps(base,indent=1),encoding='utf-8')
        proof = ROOT/'work/ui/movies/karaoke'
        proof.mkdir(parents=True,exist_ok=True)
        (proof/(movie+'.timing.json')).write_text(json.dumps(base,indent=1),encoding='utf-8')
        print(movie,len(ordered),'sung rows,',len(omitted),'omitted,',ordered[0]['start'],'to',ordered[-1]['end'])


if __name__ == '__main__':
    main()
