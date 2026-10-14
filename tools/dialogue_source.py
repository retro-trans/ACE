"""In-mission dialogue: containers, fonts and export.

Mission text lives in ``\\target\\fe\\InGame\\bnd\\InGameNNN.bnd`` (one per mission; 080/081 extra missions,
090/970/971/998 special). Container layout (checked on all 55):

    u32 0x100, u32 total size, list0, list1, list2, main_table, 0, counts (bytes: list0, list1, list2 rows)
    Each list holds 16-byte rows (unit id, FMG offset, 0, 0): one-entry name tables for lock-on labels.

``main_table`` (offset 20) points at the FMG holding objectives and dialogue. As in ACE 3, a longer table can be
appended to the container and the pointer redirected; the unit-name tables are referenced by their own rows.

Dialogue control tokens: <on()> <off()> window on/off, <op()> <ed()> open/close a radio exchange,
<sp(n)> typing speed, <ab(n)> wait n ms before advancing, <ab(0)> continue immediately.

The in-mission font is resource 50070 (CCM, 18-unit cell) with atlas 50050 (1024x512 PSMT4, GS-swizzled) inside
``\\target\\fe\\InGame\\param\\Fe1p.bnd`` (one player) and ``Fe2p.bnd`` (split screen). Those use the unnamed BND
variant: ``BND\\0``, total, count, 0, then (id, offset) pairs from byte 16.

    python tools/dialogue_source.py           # writes work/source/dialogue_ja.json (git-ignored) + limits
"""
import json
import re
import struct
from ace_formats import ROOT, SOURCE_ISO, Font, fmg_read, iso_files, require, u32

OUT = ROOT / 'work/source/dialogue_ja.json'
TOKEN = re.compile(r'<[a-z]+\([^)]*\)>')
FMG_MAGIC = bytes([0, 0, 1, 0])


def open_data():
    from build import DataBin
    f = open(SOURCE_ISO, 'rb')
    r = iso_files(f)['/DATA.BIN']
    return f, DataBin(f, r['offset'], r['size'])


def container(data):
    """Return (main table offset or 0, [(name id, FMG offset)]). Header words 8/12/16 point at three lists of
    16-byte (id, offset, 0, 0) rows; bytes 28-30 hold their row counts (as the message-system initializer at
    EE 0x2363b0 reads them). Word 20 is the main table; word 24 an optional extra table."""
    require(u32(data, 0) == 0x100 and u32(data, 4) == len(data), 'Not a mission text container')
    names = []
    for n, at in enumerate((u32(data, 8), u32(data, 12), u32(data, 16))):
        for k in range(data[28 + n] if at else 0):
            ident, off = struct.unpack_from('<II', data, at + 16 * k)
            if data[off:off + 4] == FMG_MAGIC and (ident, off) not in names:
                names.append((ident, off))
    if u32(data, 24) and data[u32(data, 24):u32(data, 24) + 4] == FMG_MAGIC:
        names.append((-1, u32(data, 24)))
    return u32(data, 20), names


def unnamed_bnd(data):
    """Children of the unnamed BND variant as {id: (offset, size)}."""
    require(data[:4] == b'BND\0', 'Not a BND')
    total, count = u32(data, 4), u32(data, 8)
    rows = [struct.unpack_from('<II', data, 16 + i * 8) for i in range(count)]
    starts = sorted([o for _, o in rows] + [total])
    return {i: (o, min(s for s in starts if s > o) - o) for i, o in rows}


def ingame_font(data):
    kids = unnamed_bnd(data)
    o, n = kids[50070]
    ccm = data[o:o + u32(data, o + 4)]
    o, n = kids[50050]
    tm2 = data[o:o + u32(data, o)]
    return Font(ccm, tm2)


def visible(text):
    return TOKEN.sub('', text)


def main():
    f, db = open_data()
    missions = []
    font = None
    for e in db.entries:
        name = e['name']
        if name.endswith('Fe1p.bnd'):
            font = ingame_font(db.read(e))
        m = re.search(r'InGame(\d+)\.bnd$', name)
        if not m:
            continue
        data = db.read(e)
        main_at, names = container(data)
        rows = fmg_read(data[main_at:main_at + u32(data, main_at + 4)]) if main_at else {}
        units = [{'id': i, 'ja': fmg_read(data[o:o + u32(data, o + 4)])} for i, o in names]
        missions.append({'mission': m.group(1), 'rows': [{'id': k, 'ja': v} for k, v in sorted(rows.items()) if v],
                         'units': [{'id': u['id'], 'ja': v} for u in units for v in u['ja'].values() if v]})
    f.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(missions, ensure_ascii=False, indent=1), encoding='utf-8')
    # Limits measured from the Japanese.
    widths, lines, sizes, missing = [], [], [], set()
    for ms in missions:
        for r in ms['rows']:
            text = visible(r['ja'])
            ls = text.split('\n')
            lines.append((len(ls), ms['mission'], r['id']))
            sizes.append((len(r['ja'].encode('cp932')), ms['mission'], r['id']))
            for l in ls:
                w = 0
                for c in l:
                    g = font.glyph(c)
                    if g is None:
                        missing.add(c)
                        continue
                    w += g['bearing'] + g['advance']
                widths.append((w, ms['mission'], r['id']))
    widths.sort(reverse=True)
    lines.sort(reverse=True)
    sizes.sort(reverse=True)
    print('missions', len(missions), 'rows', sum(len(m['rows']) for m in missions))
    print('widest lines', widths[:6])
    print('most lines', lines[:6])
    print('largest rows (bytes)', sizes[:4])
    print('characters missing from font 50070', ''.join(sorted(missing)))
    print('->', OUT)


if __name__ == '__main__':
    main()
