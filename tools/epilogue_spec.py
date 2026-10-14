"""Replace the ending's Japanese opening scroll with the existing English translation."""
import json
import movie_text as mt


def build():
    path = mt.SPEC/'MOVIE002.json'
    spec = json.loads(path.read_text(encoding='utf-8'))
    source = json.loads((mt.SPEC/'captions/MOVIE002.json').read_text(encoding='utf-8'))
    # Source scroll block coordinates; only geometry is stored here, not Japanese script.
    groups = [(379,434),(479,534),(545,601),(612,668),(678,767),
              (811,867),(877,933),(977,1068),(1110,1167)]
    lines = []
    for row,(y0,y1) in zip(source['rows'],groups):
        # One erase band per paragraph covers all original lettering, including antialiasing.
        lines.append({'band':[y0,y1],'span':[72,480]})
        face = {'size':15,'weight':600}
        parts = []
        for paragraph in row['en'].splitlines():
            parts.extend(paragraph[a:b] for a,b in mt.lyric_wrap(paragraph,face,388))
        pitch = (y1-y0)/len(parts)
        mt.require(pitch >= 18,'Epilogue translation is too tall')
        for i,text in enumerate(parts):
            lines.append(dict(face,band=[round(y0+i*pitch),round(y0+(i+1)*pitch)],
                              en=text,x=74,width=388))
    epilogue = {'id':'ending_epilogue','frames':[780,2700],'plate':[800,2690],
                'level':[20,20,70,420],'region':[72,480],'speed':.5915,'origin':800,
                'fade':[52,88,340,380],'colour':[190,128,128],'width':388,
                'lines':lines}
    spec['segments'] = [epilogue]+[s for s in spec['segments']
        if s.get('type') != 'caption' and s.get('id') != 'ending_epilogue']
    spec['note'] = 'Ending: English epilogue scroll, translated credits and full-width song karaoke overlay.'
    path.write_text(json.dumps(spec,ensure_ascii=False,indent=1),encoding='utf-8')
    print('Ending epilogue:',len(source['rows']),'paragraphs,',sum(bool(l.get('en')) for l in lines),'English lines')


if __name__ == '__main__':
    build()
