"""Check actual lyric layouts, coverage and highlight timing without printing or saving lyric text."""
import json
import numpy as np
import movie_text as mt


def check(movie):
    spec = json.loads((mt.SPEC/(movie+'.json')).read_text(encoding='utf-8'))
    song = [s for s in spec['segments'] if s.get('type') == 'karaoke']
    captions = [s for s in spec['segments'] if s.get('type') == 'lyrics_caption']
    rows = mt.read_lyrics(mt.ROOT/song[0]['lyrics'])
    expected = set(range(len(rows)))-set(spec['karaoke_review']['omitted_rows'])
    assert len(song) == len(expected) and {s['index'] for s in song} == expected
    assert all(a['frames'][1] <= b['frames'][0] for a,b in zip(song,song[1:]))
    assert all(a['frames'][1] <= b['frames'][0] for a,b in zip(captions,captions[1:]))
    rendered_captions = [(s,mt.LyricsCaption(movie,None,0,s)) for s in captions]
    bounds = []
    for s in song:
        k = mt.Karaoke(movie,None,0,s)
        assert len(k.ranges) > 0 and not k.too_wide
        assert k.progress(k.b-4) == 1.0
        assert all(a[0] < b[0] and a[1] <= b[1] for a,b in zip(s['knots'],s['knots'][1:]))
        matching = [c for t,c in rendered_captions if c.a <= k.a and c.b >= k.b and
                    rows[t['index']][1] == rows[s['index']][1]]
        assert len(matching) == 1, (movie,s['index'],'translation coverage')
        c = matching[0]
        assert k.ranges[-1][1] < c.ranges[0][0], (movie,s['index'],'overlap')
        mask = np.maximum(k.edge_r,c.edge)
        yy,xx = np.where(mask > .01)
        assert xx.min() > 0 and xx.max() < mt.W-1 and yy.min() > 0 and yy.max() < mt.H-1
        if spec['karaoke_review']['layout'] == 'strip':
            assert xx.min() >= 35 and xx.max() <= 210, (movie,s['index'],'credit panel overlap')
        if spec['karaoke_review']['layout'] == 'overlay':
            assert k.backdrop is not None and k.backdrop.shape == (mt.H,mt.W)
            assert s['backdrop']['top'] < yy.min() and yy.max() < s['backdrop']['bottom']
        bounds.append({'row':s['index'],'frames':[k.a,k.b],
                       'bounds':[int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1],
                       'romaji_lines':len(k.ranges),'english_lines':len(c.ranges)})
    result = {'movie':movie,'spec':mt.spec_hash(movie),'sung_rows':len(song),
              'translation_captions':len(captions),'omitted_rows':sorted(set(range(len(rows)))-expected),
              'checks':'coverage, non-overlap, full highlight, frame bounds and selected layout checks passed',
              'rows':bounds}
    out = mt.ROOT/'work/ui/movies/karaoke'/(movie+'.layout.json')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=1),encoding='utf-8')
    print(movie,len(song),'sung rows,',len(captions),'translation captions: layout checks passed')


if __name__ == '__main__':
    for name in ('MOVIE003','MOVIE002'):
        check(name)
