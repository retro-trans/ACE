"""Create (or extend) per-mission dialogue translation files with translator context.

    python tools/dialogue_prepare.py 001 002 ...

For each mission writes work/translation/en/dialogue/mNNN.json (git-ignored; holds Japanese) with
  context.briefing_ja  - the mission's menu table fNNN.fmg (name, objectives, failure line)
  context.flow_chart   - the matching akurasu.net flow-chart block (English mission name, conditions, units)
  units                - lock-on name labels (drawn with the 13px HUD font, which has no Latin yet: not translated)
  rows                 - [{id, ja, en, notes}] for the main table (objectives and dialogue)
Existing English is never overwritten.
"""
import json
import re
import sys
import unicodedata
from ace_formats import ROOT, bnd_child, bnd_entries, fmg_read, unpack
from dialogue_layout import DIR

SOURCE = ROOT / 'work/source/dialogue_ja.json'
FLOW = ROOT / 'work/glossary/akurasu/ACE_Flow_Chart.wiki'


def norm(s):
    return re.sub(r'[\s・･:：\-－―]', '', unicodedata.normalize('NFKC', s or ''))


def flow_blocks():
    text = FLOW.read_text(encoding='utf-8')
    return [b for b in re.split(r'\|\s*class="fc-std-sc"\s*\|', text)[1:]]


def briefing_tables():
    from dialogue_source import open_data
    f, db = open_data()
    e = next(x for x in db.entries if x['name'].endswith('MenuCampaign.csc'))
    bundle = unpack(db.read(e))
    f.close()
    out = {}
    for c in bnd_entries(bundle):
        m = re.search(r'fmg\\f(\d{3})\.fmg$', c['name'])
        if m and int(m.group(1)) < 100:
            out[m.group(1)] = fmg_read(bundle[c['offset']:c['offset'] + c['size']])
    return out


def main():
    want = sys.argv[1:]
    src = {m['mission']: m for m in json.loads(SOURCE.read_text(encoding='utf-8'))}
    briefs = briefing_tables()
    blocks = flow_blocks()
    DIR.mkdir(parents=True, exist_ok=True)
    for mission in want:
        ms = src[mission]
        brief = briefs.get(mission, {})
        name = brief.get(1) or ''
        flow = next((b for b in blocks if name and norm(name) in norm(b.split('<br>')[0])), '')
        flow = re.sub(r"'''|<br>|<span[^>]*>|</span>", ' ', flow.split('|-', 2)[0] + (flow.split('|-', 2)[1] if '|-' in flow else ''))
        path = DIR / ('m%s.json' % mission)
        old = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'rows': []}
        done = {r['id']: r for r in old['rows']}
        rows = []
        for r in ms['rows']:
            prev = done.get(r['id'], {})
            require_same = prev.get('ja') in (None, r['ja'])
            if not require_same:
                raise SystemExit('Source changed for m%s id %d' % (mission, r['id']))
            rows.append({'id': r['id'], 'ja': r['ja'], 'en': prev.get('en', ''), 'notes': prev.get('notes', '')})
        data = {'mission': mission,
                'context': {'briefing_ja': {str(k): v for k, v in brief.items() if v},
                            'flow_chart': re.sub(r'\s+', ' ', flow).strip()},
                'units': [{'id': u['id'], 'ja': u['ja']} for u in ms['units']],
                'rows': rows}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        print(path.name, len(rows), 'rows;', 'flow chart matched' if flow.strip() else 'NO flow chart match')


if __name__ == '__main__':
    main()
