"""Verify translated movies and unchanged soundtracks. Use --original-story for builds 0.1.16-0.1.23."""
import argparse
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


def verify(iso, original_story=False):
    build_report = json.loads(iso.with_suffix('.json').read_text(encoding='utf-8'))
    overlay = build_report.get('movie_overlay')
    if overlay:
        require(overlay['card_count'] == 171 and len(overlay['movies']) == 22,
                'Incomplete runtime story captions')
        require(not build_report.get('movies_without_lyrics'), 'Overlay build must retain lyrics')
        original_story = True
    allowed = {mt.disc_path(n) for n in ('MOVIE001','MOVIE002','MOVIE003')}
    expected_story = {mt.disc_path('M1_MOVIE%03d' % n) for n in range(1, 23)}
    if not original_story:
        allowed |= expected_story
    wanted = set(build_report['movies'])
    # A release build without song lyrics (build.py --no-lyrics) leaves a lyrics-only movie original.
    require(wanted <= allowed and (wanted == allowed or build_report.get('movies_without_lyrics')),
            'Unexpected translated movie scope')
    no_lyrics = bool(build_report.get('movies_without_lyrics'))
    require((wanted & expected_story) == (set() if original_story else expected_story),
            'Unexpected story movie scope')
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
                movie = ('M1_' if name.startswith('/MOVIE1/') else '') + Path(name).stem
                src,dst = mt.source_movie(movie),mt.OUT/(movie+'.PSS')
                if no_lyrics and (mt.OUT/(movie+'.nolyrics.PSS')).exists():
                    dst = mt.OUT/(movie+'.nolyrics.PSS')
                pacing = build_report.get('movie_pacing', {}).get(name)
                if pacing:
                    import movie_pacing
                    require(movie_pacing.file_hash(dst) == pacing['source_sha256'], 'Pacing source mismatch: '+movie)
                    dst = iso.parent/'movie-pacing'/dst.name
                    require(pacing.get('decoded_frames_verified', 0) > 0, 'Unverified pacing movie: '+movie)
                with open(dst,'rb') as stream:
                    require(range_hash(stream,0,dst.stat().st_size) == actual,'Built movie file mismatch: '+movie)
                packets = mt.video_packets(src)
                if not pacing:
                    require(packets == mt.video_packets(dst),'Packet positions changed: '+movie)
                else:
                    # Repacking only splits original video PES ranges into shorter
                    # video PES + padding packets. Original audio/pack ranges stay
                    # at exactly the same offsets and are hashed below.
                    with dst.open('rb') as f:
                        import mmap
                        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
                            list(movie_pacing.packets(data))
                before,after = nonvideo_hash(src,packets),nonvideo_hash(dst,packets)
                require(before == after,'Audio or nonvideo bytes changed: '+movie)
                results[name] = {'status':'translated','sha256':actual,'nonvideo_sha256':after}
            else:
                require(actual == range_hash(original,old['offset'],old['size']),
                        'Original movie was not restored: '+name)
                results[name] = {'status':'original','sha256':actual}
    story = [n for n in results if n.startswith('/MOVIE1/')]
    require(set(story) == expected_story,'Expected 22 story movies')
    translated_story = sum(results[n]['status'] == 'translated' for n in story)
    report = {'iso':iso.name,'translated_movies':sorted(wanted),'original_story_movies':22-translated_story,
              'translated_story_movies':translated_story,
              'runtime_translated_story_movies': 22 if overlay else 0,
              'audio_and_nonvideo_unchanged':True,'movies':results}
    target = iso.with_suffix('.movies.verify.json')
    target.write_text(json.dumps(report,indent=1),encoding='utf-8')
    print('PASS: %d translated movies, %d translated / %d original story movies; all audio and nonvideo bytes unchanged'
          % (len(wanted), translated_story, 22-translated_story))
    if overlay:
        print('All 22 original story movies have runtime English caption tables (171 cards).')
    print('Report:',target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--original-story', action='store_true')
    args = parser.parse_args()
    verify(args.iso, args.original_story)
