"""Check every replaced epilogue frame for surviving Japanese strokes, excluding the new English."""
import json
import numpy as np
import movie_text as mt


def main():
    data = json.loads((mt.SPEC/'MOVIE002.json').read_text(encoding='utf-8'))
    index, spec = next((i,s) for i,s in enumerate(data['segments']) if s.get('id') == 'ending_epilogue')
    original = mt.CACHE/'MOVIE002.m2v'
    encoded = mt.CACHE/'MOVIE002.new.m2v'
    report = json.loads((mt.OUT/'MOVIE002.json').read_text(encoding='utf-8'))
    mt.require(report['spec'] == mt.spec_hash('MOVIE002'),'Ending movie is stale')
    seg = mt.Segment('MOVIE002',original,index,spec)
    failures, worst, checked, pixels = [], 0.0, 0, 0
    for (n,old),(_,new) in zip(mt.frames(original,seg.a,seg.b),mt.frames(encoded,seg.a,seg.b)):
        before,after = mt.planes(old)[0],mt.planes(new)[0]
        bg = seg.background(n,before)[0]
        english = mt.dilate(seg.window(seg.text,n)>.015,3)
        source_strokes = (before-bg > 30) & (before-mt.box(before,3)>25)
        region = np.zeros((mt.H,mt.W),bool)
        region[45:392,72:480] = True
        test = source_strokes & region & ~english
        checked += 1
        if test.sum() < 20:
            continue
        count = int(test.sum())
        pixels += count
        share = float((np.abs(after[test]-bg[test])>18).mean())
        worst = max(worst,share)
        if share > .05:
            failures.append({'frame':n,'surviving_share':round(share,4),'pixels':count})
    result = {'movie':'MOVIE002','spec':report['spec'],'frames_checked':checked,
              'source_stroke_pixels_checked':pixels,'worst_surviving_share':round(worst,4),
              'n_failing':len(failures),'failing_frames':failures}
    out = mt.ROOT/'work/ui/movies/epilogue.verify.json'
    out.write_text(json.dumps(result,indent=1),encoding='utf-8')
    print('Epilogue:',checked,'frames,',len(failures),'failures; worst surviving stroke share',round(worst,4))
    mt.require(not failures,'Review epilogue frames listed in '+str(out))


if __name__ == '__main__':
    main()
