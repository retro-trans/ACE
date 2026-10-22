"""Add a verified upgrade route without changing published game/patch bytes.

Writes a separate local package; uploading its metadata is an explicit later step.
Run with Python 3.11+. Defaults to a dry run.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from package_release import ROOT, UPSTREAM, PIN, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--from-version', required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    version, previous = args.version, args.from_version
    original = ROOT / ('work/output/release-' + version)
    output = ROOT / ('work/output/release-%s-upgrade-from-%s' % (version, previous))
    upgrade = ROOT / ('work/output/upgrade-%s-to-%s' % (previous, version))
    manifest = json.loads((original / 'BUILD-MANIFEST.json').read_text(encoding='utf-8'))
    old_manifest = json.loads((ROOT / ('docs/releases/' + previous + '/BUILD-MANIFEST.json')).read_text(encoding='utf-8'))
    source_row = old_manifest['patches'][0]
    target_row = manifest['patches'][0]
    assert manifest['version'] == version and old_manifest['version'] == previous
    assert all(p['target_sha256'] == target_row['target_sha256'] and p['target_bytes'] == target_row['target_bytes'] for p in manifest['patches'])
    assert all(p['target_sha256'] == source_row['target_sha256'] and p['target_bytes'] == source_row['target_bytes'] for p in old_manifest['patches'])
    if any(p['source_version'] == previous for p in manifest['patches']):
        parser.error('Upgrade route already exists')
    source = ROOT / ('work/output/ACE-EN-%s.iso' % previous)
    target = ROOT / ('work/output/ACE-EN-%s.iso' % version)
    name = 'ACE-English-%s-to-%s.xdelta' % (previous, version)
    config = {k: manifest[k] for k in ('game_id', 'game_name', 'platform', 'version', 'source_commit')}
    config['patches'] = [dict(patch=name, edition='English', language='en',
        source_version=previous, source_format='iso', target_format='iso',
        source=str(source), target=str(target))]
    print(json.dumps(config, indent=2), flush=True)
    if not args.write:
        print('Dry run: repeat with --write to build and verify the upgrade.')
        return
    if output.exists() or upgrade.exists():
        parser.error('Output already exists; refusing to overwrite')
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=UPSTREAM, text=True).strip() != PIN:
        parser.error('Retro Trans Tools must be at reviewed revision ' + PIN)
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=UPSTREAM, text=True).strip():
        parser.error('Retro Trans Tools has modified tracked files')
    sys.path.insert(0, str(UPSTREAM))
    from retro_trans.release import build_release, validate_directory
    from retro_trans.catalog import atomic_json
    from retro_trans.core import sha256_file
    validate_directory(original)
    identities = {}
    for path, row in ((source, source_row), (target, target_row)):
        print('Checking published image: ' + path.name, flush=True)
        identities[path] = hashes(path)
        if path.stat().st_size != row['target_bytes'] or identities[path]['sha256'] != row['target_sha256']:
            raise ValueError('Image differs from published identity: ' + path.name)
        if row.get('target_sha1') and identities[path]['sha1'] != row['target_sha1']:
            raise ValueError('Published SHA-1 differs: ' + path.name)
    private = ROOT / ('work/source/upgrade-%s-to-%s-local.json' % (previous, version))
    private.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    last = [0.0, '']

    def progress(message, fraction=None):
        now = time.monotonic()
        if message != last[1] or now - last[0] > 20:
            print(message + ((' %.0f%%' % (fraction * 100)) if fraction is not None else ''), flush=True)
            last[:] = [now, message]

    built = build_release(private, upgrade, progress=progress)
    row = built['patches'][0]
    assert row['source_sha256'] == source_row['target_sha256']
    assert row['target_sha256'] == target_row['target_sha256']
    row['source_sha1'] = identities[source]['sha1']
    row['target_sha1'] = identities[target]['sha1']
    # Preserve every existing patch entry and byte; only append the new route.
    manifest['patches'].append(row)
    output.mkdir()
    for patch in manifest['patches']:
        origin = upgrade if patch['patch'] == name else original
        shutil.copyfile(origin / patch['patch'], output / patch['patch'])
    atomic_json(output / 'BUILD-MANIFEST.json', manifest)
    validation = json.loads((original / 'VALIDATION.json').read_text(encoding='utf-8'))
    validation['patches'].extend(json.loads((upgrade / 'VALIDATION.json').read_text(encoding='utf-8'))['patches'])
    validation['manifest_sha256'] = sha256_file(output / 'BUILD-MANIFEST.json')
    atomic_json(output / 'VALIDATION.json', validation)
    sums = ['{}  {}'.format(sha256_file(p), p.name) for p in sorted(output.iterdir())]
    (output / 'SHA256SUMS.txt').write_text('\n'.join(sums) + '\n', encoding='utf-8')
    validate_directory(output)
    print('Verified augmented package: ' + str(output), flush=True)


if __name__ == '__main__':
    main()
