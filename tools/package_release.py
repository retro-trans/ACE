"""Package a verified ISO using the pinned Retro Trans release builder.

Run with Python 3.11+. Defaults to a dry run; --write encodes and round-trips.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / 'work/source/retro-trans-tools'
PIN = 'dde06f13fdabd7d9fa03af861f50e72fcf196faa'
SOURCE = ROOT / "Another Century's Episode (Japan).iso"
SOURCE_SHA256 = '7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9'


def hashes(path):
    digests = {name: hashlib.new(name) for name in ('sha256', 'sha1')}
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            for digest in digests.values():
                digest.update(chunk)
    return {name: digest.hexdigest() for name, digest in digests.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--version', required=True, help='e.g. 0.1.21 (packages work/output/ACE-EN-<version>.iso)')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    VERSION = args.version
    TARGET = ROOT / ('work/output/ACE-EN-%s.iso' % VERSION)
    report = json.loads((ROOT / ('work/output/ACE-EN-%s.json' % VERSION)).read_text(encoding='utf-8'))
    EXPECTED = {SOURCE: SOURCE_SHA256, TARGET: report['sha256']}
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', args.source_commit + '^{commit}'], cwd=ROOT, text=True).strip()
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=UPSTREAM, text=True).strip()
    if actual != PIN:
        parser.error('Retro Trans Tools must be at reviewed revision ' + PIN)
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=UPSTREAM, text=True).strip():
        parser.error('Retro Trans Tools has modified tracked files')
    config = dict(game_id='ace', game_name="Another Century's Episode", platform='PS2',
                  version=VERSION, source_commit=commit, patches=[dict(
                      patch='ACE-English-%s.xdelta' % VERSION, edition='English', language='en',
                      source_version='original', source_format='iso', target_format='iso',
                      source=str(SOURCE), target=str(TARGET))])
    print(json.dumps(config, indent=2), flush=True)
    if not args.write:
        print('Dry run: verify the inputs above, then repeat with --write.')
        return
    output = ROOT / ('work/output/release-' + VERSION)
    if output.exists():
        parser.error('Release output already exists; never overwrite published assets')
    identities = {}
    for path, expected in EXPECTED.items():
        print('Checking ' + path.name, flush=True)
        identities[path] = hashes(path)
        if identities[path]['sha256'] != expected:
            parser.error('Unexpected image identity: ' + path.name)
    private = ROOT / ('work/source/release-%s-local.json' % VERSION)
    private.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    sys.path.insert(0, str(UPSTREAM))
    from retro_trans.release import build_release, validate_directory
    from retro_trans.catalog import atomic_json
    from retro_trans.core import sha256_file
    last = [0.0, '']

    def progress(message, fraction=None):
        now = time.monotonic()
        if message != last[1] or now - last[0] > 20:
            print(message + ((' %.0f%%' % (fraction * 100)) if fraction is not None else ''), flush=True)
            last[:] = [now, message]

    manifest = build_release(private, output, progress=progress)
    row = manifest['patches'][0]
    if row['source_sha256'] != EXPECTED[SOURCE] or row['target_sha256'] != EXPECTED[TARGET]:
        raise RuntimeError('Release builder returned an unexpected binary identity')
    row['source_sha1'] = identities[SOURCE]['sha1']
    row['target_sha1'] = identities[TARGET]['sha1']
    atomic_json(output / 'BUILD-MANIFEST.json', manifest)
    validation_path = output / 'VALIDATION.json'
    validation = json.loads(validation_path.read_text(encoding='utf-8'))
    validation['manifest_sha256'] = sha256_file(output / 'BUILD-MANIFEST.json')
    atomic_json(validation_path, validation)
    sums = ['{}  {}'.format(sha256_file(p), p.name) for p in sorted(output.iterdir()) if p.name != 'SHA256SUMS.txt']
    (output / 'SHA256SUMS.txt').write_text('\n'.join(sums) + '\n', encoding='utf-8')
    validate_directory(output)
    records = ROOT / ('docs/releases/' + VERSION)
    records.mkdir(parents=True, exist_ok=True)
    for name in ('BUILD-MANIFEST.json', 'VALIDATION.json', 'SHA256SUMS.txt'):
        shutil.copyfile(output / name, records / name)
    print('Verified release package: ' + str(output), flush=True)


if __name__ == '__main__':
    main()
