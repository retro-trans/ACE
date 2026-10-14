"""Inventory of Japanese text left on a disc image: every FMG text table in every DATA.BIN resource (plain, packed,
and nested), referenced or not, grouped by identical content.

    python tools/japanese_inventory.py [iso]      # default: newest work/output/ACE-EN-*.iso
Writes work/source/japanese_inventory.json (git-ignored; contains Japanese) and prints a summary.
"""
import collections
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from ace_formats import ROOT, fmg_read, is_packed, iso_files, unpack

JP = re.compile(r'[぀-ヿ一-鿿]')
TOKEN = re.compile(r'<[a-z]+\([^)]*\)>|#c(\[[0-9A-Fa-f]{6}\])?')
MAGIC = bytes([0, 0, 1, 0])


def tables_in(data):
    """(offset, rows) for each well-formed FMG table found anywhere in ``data``."""
    out, at = [], 0
    while True:
        at = data.find(MAGIC, at)
        if at < 0:
            return out
        try:
            size, zero, groups, count, table, reserved = struct.unpack_from('<6I', data, at + 4)
            ok = not zero and not reserved and 0 < groups <= count < 20000 and table == 28 + 12 * groups \
                and table + count * 4 <= size and at + size <= len(data)
            rows = fmg_read(data[at:at + size]) if ok else None
        except Exception:
            rows = None
        if rows and any(v for v in rows.values()):
            out.append((at, rows))
            at += size
        else:
            at += 4


def main():
    from build import DataBin
    iso = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((ROOT / 'work/output').glob('ACE-EN-*.iso'))[-1]
    groups = collections.OrderedDict()
    with open(iso, 'rb') as f:
        r = iso_files(f)['/DATA.BIN']
        db = DataBin(f, r['offset'], r['size'])
        for e in db.entries:
            data = db.read(e)
            if is_packed(data):
                try:
                    data = unpack(data)
                except Exception:
                    continue
            found = tables_in(data)
            children = []
            if data[:4] == b'BND' + bytes(1):
                try:
                    from ace_formats import bnd_entries
                    children = bnd_entries(data)
                except Exception:
                    children = []
            for at, rows in found:
                child = next((c['name'] for c in children if c['offset'] <= at < c['offset'] + c['size']), None)
                jp = {i: v for i, v in rows.items() if v and JP.search(TOKEN.sub('', v))}
                if not jp:
                    continue
                key = hashlib.sha1(json.dumps(sorted(jp.items()), ensure_ascii=False).encode()).hexdigest()[:12]
                g = groups.setdefault(key, {'rows': jp, 'where': []})
                g['where'].append('%s%s@%#x' % (e['name'], (':' + child) if child else '', at))
    out = [{'key': k, 'where': g['where'], 'rows': {str(i): v for i, v in sorted(g['rows'].items())}} for k, g in groups.items()]
    path = ROOT / 'work/source/japanese_inventory.json'
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    total = sum(len(g['rows']) for g in out)
    print('image:', iso.name)
    print('distinct tables with Japanese:', len(out), 'rows:', total)
    for g in sorted(out, key=lambda g: -len(g['rows'])):
        print('%4d rows  x%-2d  %s' % (len(g['rows']), len(g['where']), g['where'][0].split('\\')[-1]))


if __name__ == '__main__':
    main()
