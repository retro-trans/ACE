"""Create a narrowly scoped dialogue-isolation ISO from an existing local build.

Restores original dialogue (ids >= 10) for one internal mission; keeps the English
objectives, lock-on labels, all other game data, movies and audio. Updates the title
version. Does not edit translation sources or publish a release. Dry run by default.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from ace_formats import ROOT, SOURCE_ISO, bnd_replace, fmg_build, fmg_read, pack, require, u32, unpack
from texture_text import SPEC, apply_spec
from title_stamp import TEXTURE, stamp_texture
from verify_title_stamp import database, leaf, children


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def table(body):
    at = u32(body, 20)
    return at, fmg_read(body[at:at + u32(body, at + 4)])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--version', required=True)
    ap.add_argument('--mission', required=True, help='Internal mission id, e.g. 025 for campaign mission 23')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    require(args.baseline != args.version, 'Use a distinct diagnostic build version')
    baseline = ROOT / ('work/output/ACE-EN-' + args.baseline + '.iso')
    output = ROOT / ('work/output/ACE-EN-' + args.version + '-dialogue-diagnostic.iso')
    build = json.loads(baseline.with_suffix('.json').read_text(encoding='utf-8'))
    target = 'InGame' + args.mission + '.bnd'
    require(not output.exists(), 'Diagnostic output already exists; will not overwrite it')
    patches, expected, changed = {}, {}, []
    with SOURCE_ISO.open('rb') as sf, baseline.open('rb') as bf:
        source, base = database(sf), database(bf)
        originals = {e['name']: e for e in source.entries}
        original = source.read(next(e for e in source.entries if leaf(e['name']) == target))
        _, japanese = table(original)
        original_tex = source.read(next(e for e in source.entries if leaf(e['name']) == TEXTURE))
        spec = json.loads((SPEC / 't3105_tm2.json').read_text(encoding='utf-8'))
        _, artwork = apply_spec(original_tex, spec)
        title, stamp = stamp_texture(original_tex, artwork, args.version)
        header = bytearray(base.header)
        starts = sorted({e['offset'] for e in base.entries} | {base.size})
        restored_ids, matching_logic = [], []
        for e in base.entries:
            name = leaf(e['name'])
            body = base.read(e)
            new = None
            if name == target:
                at, english = table(body)
                require(english.keys() == japanese.keys(), 'Dialogue row IDs differ from original')
                rows = {ident: japanese[ident] if ident >= 10 else text for ident, text in english.items()}
                restored_ids = [ident for ident in rows if rows[ident] != english[ident]]
                encoded = fmg_build(rows)
                size = u32(body, at + 4)
                require(len(encoded) <= size, 'Original dialogue does not fit the existing table slot')
                new = body[:at] + encoded + bytes(size - len(encoded)) + body[at + size:]
                require(table(new)[1] == rows, 'Diagnostic table failed round trip')
                require(new[:at] == body[:at] and new[at + size:] == body[at + size:],
                        'Non-dialogue container data changed')
            elif name == TEXTURE:
                new = title
            elif name in ('MenuTitle.csc', 'MenuTitleIntro.csc'):
                raw = unpack(body)
                new = pack(bnd_replace(raw, {TEXTURE: title}))
                before, after = children(body), children(new)
                require(before.keys() == after.keys(), 'Title bundle resource list changed')
                require(all(after[k] == (title if leaf(k) == TEXTURE else before[k]) for k in before),
                        'Unrelated title bundle data changed')
            if ('\\com\\logic\\' in e['name'] or name in
                    ('map' + args.mission + '.src', 'map' + args.mission + '.csc') or
                    ('\\m' + args.mission + '\\') in e['name']):
                require(body == source.read(originals[e['name']]), 'Mission logic differs from original: ' + e['name'])
                matching_logic.append(e['name'])
            if new is None:
                continue
            slot = min(s for s in starts if s > e['offset']) - e['offset']
            require(len(new) <= slot, 'Modified resource does not fit its slot: ' + name)
            # Only touch the occupied bytes; preserve all remaining archive padding.
            occupied = max(e['size'], len(new))
            patches[base.base + e['offset']] = new + bytes(occupied - len(new))
            struct.pack_into('<I', header, 32 + e['index'] * 16 + 8, len(new))
            expected[e['name']] = new
            changed.append(e['name'])
        require(len(changed) == 4 and restored_ids, 'Expected mission dialogue plus three title copies')
        patches[base.base] = bytes(header)
    report = dict(version=args.version, diagnostic=True, baseline=baseline.name,
                  baseline_sha256=build['sha256'], internal_mission=args.mission,
                  restored_dialogue_ids=restored_ids, changed_resources=changed,
                  original_logic_resources_verified=len(matching_logic), title_stamp=stamp,
                  gameplay_verified=False, root_cause_confirmed=False)
    print(json.dumps(report, indent=2), flush=True)
    if not args.write:
        print('Dry run. Repeat with --write to create the diagnostic ISO.')
        return
    require(digest(baseline) == build['sha256'], 'Baseline ISO hash mismatch')
    intervals = sorted((offset, offset + len(data), data) for offset, data in patches.items())
    require(all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])), 'Overlapping patch ranges')
    # Exclusive creation; original ISO and submitted memory card are never opened for writing.
    with baseline.open('rb') as src, output.open('xb') as dst:
        for block in iter(lambda: src.read(8 << 20), b''):
            dst.write(block)
        for offset, _, data in intervals:
            dst.seek(offset)
            dst.write(data)
    # Verify every byte, including filesystem records, movies and archive padding.
    h = hashlib.sha256()
    with baseline.open('rb') as src, output.open('rb') as dst:
        position = 0
        while True:
            old, actual = src.read(8 << 20), dst.read(8 << 20)
            require(len(old) == len(actual), 'Output size changed')
            if not old:
                break
            wanted = bytearray(old)
            for start, end, data in intervals:
                lo, hi = max(start, position), min(end, position + len(old))
                if lo < hi:
                    wanted[lo - position:hi - position] = data[lo - start:hi - start]
            require(actual == wanted, 'Unexpected ISO byte changes at ' + hex(position))
            h.update(actual)
            position += len(old)
    with output.open('rb') as f:
        db = database(f)
        for e in db.entries:
            if e['name'] in expected:
                require(db.read(e) == expected[e['name']], 'Output resource mismatch')
    report.update(sha256=h.hexdigest(), bytes=output.stat().st_size,
                  all_other_iso_bytes_unchanged=True, movies_and_lyrics_unchanged=True)
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Verified diagnostic ISO: ' + str(output), flush=True)


if __name__ == '__main__':
    main()
