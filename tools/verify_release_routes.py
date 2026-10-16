"""Check an ACE release in a candidate or downloaded Retro Trans catalog."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'work/source/retro-trans-tools'))
from retro_trans.catalog import Catalog, matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, help='Inject a candidate manifest before publication')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    version, tag = args.version, 'v' + args.version
    build = json.loads((ROOT / ('work/output/ACE-EN-' + version + '.json')).read_text(encoding='utf-8'))
    data = json.loads(args.catalog.read_text(encoding='utf-8'))
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        if any(r['repo'] == 'retro-trans/ACE' and r['tag'] == tag for r in data['releases']):
            raise ValueError('Candidate version already exists in the catalog')
        assert manifest['version'] == version
        data['releases'].append(dict(repo='retro-trans/ACE', tag=tag, manifest=manifest,
            assets={p['patch']: 'https://github.com/retro-trans/ACE/releases/download/' + tag + '/' + p['patch']
                    for p in manifest['patches']}))
    catalog = Catalog(data)
    source = catalog.nodes[('ace', 'English', 'en', 'original')]
    target = catalog.nodes[('ace', 'English', 'en', version)]
    assert matches(source, {'sha256': '7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9'}, 3357147136)
    assert matches(target, {'sha256': build['sha256']}, 3357147136)
    routes = []
    for selection in ('Latest', version):
        plan = catalog.plan(source, selection)
        assert plan.target == target and len(plan.edges) == 1
        assert plan.edges[0].asset.name == 'ACE-English-' + version + '.xdelta'
        routes.append({'selection': selection, 'target': plan.target.version, 'patches': [e.asset.name for e in plan.edges]})
    # Next version intentionally chooses the earliest published version, not Latest.
    next_plan = catalog.plan(source, 'Next version only')
    assert len(next_plan.edges) == 1
    routes.append({'selection': 'Next version only', 'target': next_plan.target.version,
                   'patches': [e.asset.name for e in next_plan.edges]})
    assert not catalog.plan(target, 'Latest').edges
    assert not any(matches(node, {'sha256': '0' * 64}, 3357147136) for node in catalog.nodes.values())
    report = dict(candidate=bool(args.manifest), game_id='ace', version=version,
                  original_routes=routes, current_image_noop=True, unknown_image_rejected=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
