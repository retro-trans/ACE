"""Download the akurasu.net Another Century's Episode pages and parse them into a JP -> EN term list.

akurasu.net is the project's main source for names (see AGENTS.md). Pages are saved as raw wikitext under
work/glossary/akurasu/ so the parse can be re-run offline.

    python tools/akurasu_terms.py [--offline]
Writes work/glossary/akurasu_terms.json: [{"jp", "key", "en", "page", "section", "url"}]
"""
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from ace_formats import ROOT

PAGES = ["Another Century's Episode", "Another Century's Episode/Mech Database",
         "Another Century's Episode/Mech Abilities", "Another Century's Episode/Flow Chart",
         "Another Century's Episode/Series List", "Another Century's Episode/Mech/Carrier Upgrade",
         "Another Century's Episode/Gameplay Tips And Strategies"]
API = 'https://akurasu.net/wiki/api.php?action=parse&prop=wikitext&format=json&page='
URL = 'https://akurasu.net/wiki/'
OUT = ROOT / 'work/glossary'
JP = re.compile(r'[぀-ヿ一-鿿０-ｚ]')


def norm(s):
    """NFKC, drop spaces / middle dots / brackets so game and wiki spellings line up."""
    s = unicodedata.normalize('NFKC', s or '')
    return re.sub(r'[\s・･·=＝()（）\[\]<>＜＞〈〉]', '', s)


def fetch(page, offline):
    path = OUT / 'akurasu' / (page.replace("Another Century's Episode", 'ACE').replace('/', '_').replace(' ', '_') + '.wiki')
    if not offline:
        req = urllib.request.Request(API + urllib.parse.quote(page), headers={'User-Agent': 'Mozilla/5.0'})
        text = json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))['parse']['wikitext']['*']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    return path.read_text(encoding='utf-8')


def parse(page, text):
    terms, section = [], ''
    url = URL + urllib.parse.quote(page.replace(' ', '_'))
    for line in text.splitlines():
        h = re.match(r'^(=+)\s*(.*?)\s*\1\s*$', line)
        if h:
            title = h.group(2)
            m = re.match(r'^(.*?)\s*[(（]([^()（）]*)[)）]\s*$', title)
            if m and JP.search(m.group(2)):
                terms.append({'jp': m.group(2).strip(), 'key': norm(m.group(2)), 'en': m.group(1).strip(),
                              'page': page, 'section': section, 'url': url})
            elif len(h.group(1)) == 2:
                section = title
            continue
        # "English (Japanese)" inside table cells or list items, e.g. mission names in the flow chart.
        for m in re.finditer(r'([A-Z0-9][^|()（）\[\]{}<>]*?)\s*[(（]([^()（）|]*[぀-ヿ一-鿿][^()（）|]*)[)）]', line):
            terms.append({'jp': m.group(2).strip(), 'key': norm(m.group(2)), 'en': m.group(1).strip(' \'*:-'),
                          'page': page, 'section': section, 'url': url})
    return terms


def main():
    offline = '--offline' in sys.argv
    terms = []
    for page in PAGES:
        terms += parse(page, fetch(page, offline))
    seen, out = set(), []
    for t in terms:
        k = (t['key'], t['en'])
        if k not in seen:
            seen.add(k)
            out.append(t)
    (OUT / 'akurasu_terms.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'terms ->', OUT / 'akurasu_terms.json')


if __name__ == '__main__':
    main()
