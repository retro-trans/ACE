"""Verify rebuilt movies on disc, unchanged soundtracks, and restoration of all original story movies."""
import hashlib
import json
import sys
from pathlib import Path
from ace_formats import SOURCE_ISO, iso_files, require
import movie_text as mt


def range_hash(stream, offset, size):
    stream.seek(offset)
    digest = hashlib.sha256()
    while size:
        block = stream.read(min(size,8<<20))
        require(bool(block),'Unexpected end of file')
        digest.update(block)
        size -= len(block)
    return digest.hexdigest()


def nonvideo_hash(path, packets):
    """Everything outside video PES packets includes every original audio packet and pack header."""
    digest = hashlib.sha256()
    with open(path,'rb') as stream:
        pos = 0
        for header,payload,size,_ in packets:
            stream.seek(pos)
            left = header-pos
            while left:
                chunk = stream.read(min(left,8<<20))
                require(bool(chunk),'Unexpected end of PSS')
                digest.update(chunk)
                left -= len(chunk)
            pos = payload+size
        stream.seek(pos)
        for chunk in iter(lambda:stream.read(8<<20),b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify(iso):
    build_report = json.loads(iso.with_suffix('.json').read_text(encoding='utf-8'))
    allowed = {mt.disc_path(n) for n in ('MOVIE001','MOVIE002','MOVIE003')}
    wanted = set(build_report['movies'])
    # A release build without song lyrics (build.py --no-lyrics) leaves a lyrics-only movie original.
    require(wanted <= allowed and (wanted == allowed or build_report.get('movies_without_lyrics')),
            'Unexpected translated movie scope')
    no_lyrics = bool(build_report.get('movies_without_lyrics'))
    results = {}
    with open(SOURCE_ISO,'rb') as original, open(iso,'rb') as built:
        old_files,new_files = iso_files(original),iso_files(built)
        for name,old in sorted(old_files.items()):
            if not name.endswith('.PSS'):
                continue
            new = new_files[name]
            require(old['size'] == new['size'],'Movie size changed: '+name)
            actual = range_hash(built,new['offset'],new['size'])
            if name in wanted:
                require(actual == build_report['movies'][name],'Built movie mismatch: '+name)
                movie = Path(name).stem
                src,dst = mt.source_movie(movie),mt.OUT/(movie+'.PSS')
                if no_lyrics and (mt.OUT/(movie+'.nolyrics.PSS')).exists():
                    dst = mt.OUT/(movie+'.nolyrics.PSS')
                with open(dst,'rb') as stream:
                    require(range_hash(stream,0,dst.stat().st_size) == actual,'Built movie file mismatch: '+movie)
                packets = mt.video_packets(src)
                require(packets == mt.video_packets(dst),'Packet positions changed: '+movie)
                before,after = nonvideo_hash(src,packets),nonvideo_hash(dst,packets)
                require(before == after,'Audio or nonvideo bytes changed: '+movie)
                results[name] = {'status':'translated','sha256':actual,'nonvideo_sha256':after}
            else:
                require(actual == range_hash(original,old['offset'],old['size']),
                        'Original movie was not restored: '+name)
                results[name] = {'status':'original','sha256':actual}
    story = [n for n in results if n.startswith('/MOVIE1/')]
    require(len(story) == 22,'Expected 22 original story movies')
    report = {'iso':iso.name,'translated_movies':sorted(wanted),'original_story_movies':len(story),
              'audio_and_nonvideo_unchanged':True,'movies':results}
    target = iso.with_suffix('.movies.verify.json')
    target.write_text(json.dumps(report,indent=1),encoding='utf-8')
    print('PASS: %d translated movies,' % len(wanted), '22 original story movies; all audio and nonvideo bytes unchanged')
    print('Report:',target)


if __name__ == '__main__':
    verify(Path(sys.argv[1]))
