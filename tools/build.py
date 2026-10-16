"""Build a translated Another Century's Episode disc image.

    python tools/build.py 0.1.0            # dry run: report what would change
    python tools/build.py 0.1.0 --write    # writes work/output/ACE-EN-<version>.iso and a build report

Steps:
  1. Add the variable-width English glyph set (tools/vwf_font.py) to every copy of the main menu font f010
     (standalone resource and the seven Menu*.csc bundles).
  2. Replace the Terminology table f205.fmg (MenuCampaign, MenuFree, standalone) with the English text from
     work/translation/en/encyclopedia.json, wrapped and paginated by tools/encyclopedia_layout.py.
     Untranslated rows keep the Japanese.
  3. In-mission dialogue: add the English glyph set to the dialogue font (resource 50070/50050 in Fe1p.bnd and
     Fe2p.bnd) and, for every mission with translated rows (work/translation/en/dialogue/mNNN.json), append an
     English copy of the main text table to InGameNNN.bnd and point the container's word 20 at it. The original
     table stays in place; untranslated rows keep the Japanese.
  4. Repack changed bundles. A resource is written back in place when it fits its original DATA.BIN slot,
     otherwise appended at the end of DATA.BIN; the archive index is updated.
  5. Write the ISO in the original file order. Files after DATA.BIN shift only if DATA.BIN grew; the shift is
     absorbed by the disc's trailing padding so the image size, the trailing UDF anchor and every other file's
     bytes stay the same. ISO9660 records (both byte orders) and UDF file entries are rewritten together.
The game opens every disc file by name (CdSearchFile), so moved extents are safe.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import struct
import pycdlib
from ace_formats import (ROOT, SECTOR, SOURCE_ISO, Font, align, bnd_child, bnd_entries, bnd_replace, fix_udf_tag,
                         fmg_build, fmg_read, iso_files, pack, require, u32, unpack)
from vwf_font import add_english
import encyclopedia_layout as layout
import dialogue_layout
import briefing_layout
import re
from ui_apply import UiText, patch_small_font
from texture_apply import TextureText

FONT_BUNDLES = ('MenuTitle.csc', 'MenuIntro.csc', 'MenuTitleIntro.csc', 'MenuCampaign.csc', 'MenuFree.csc',
                'MenuMulti.csc', 'MenuEnding.csc')
TEXT_BUNDLES = ('MenuCampaign.csc', 'MenuFree.csc')
DIALOGUE_FONT_BUNDLES = ('Fe1p.bnd', 'Fe2p.bnd')
BRIEFING_TABLE = re.compile(r'\\fmg\\f(0\d\d)\.fmg$')  # mission tables f001-f081 (f000 is excluded by its file)
DIALOGUE_CCM, DIALOGUE_TM2 = 50070, 50050


def unnamed_bnd_replace(data, replacements, alignment=32):
    """Rebuild an unnamed-variant BND ("BND", total, count, 0, (id, offset) pairs) with children replaced by
    id. Children keep their order; replaced ones are padded to ``alignment`` like the originals."""
    total, count = u32(data, 4), u32(data, 8)
    rows = [struct.unpack_from('<II', data, 16 + i * 8) for i in range(count)]
    starts = sorted([o for _, o in rows] + [total])
    out = bytearray(data[:min(o for _, o in rows)])
    for index, (ident, off) in sorted(enumerate(rows), key=lambda r: r[1][1]):
        end = min(x for x in starts if x > off)
        body = data[off:end]
        if ident in replacements:
            body = replacements[ident] + bytes(-len(replacements[ident]) % alignment)
        out += bytes(-len(out) % alignment)
        struct.pack_into('<I', out, 16 + index * 8 + 4, len(out))
        out += body
    struct.pack_into('<I', out, 4, len(out))
    require(set(replacements) <= {i for i, _ in rows}, 'Unknown child id')
    return bytes(out)


HUD_CCM, HUD_TM2 = 50071, 50051
# Same-size edits outside the text tables: (VA, original CP932 bytes, replacement). The slot sizes were checked
# against the zero padding that follows each string.
ELF_STRINGS = [
    (0x2c6470, 'アナザーセンチュリーズエピソード', "Another Century's Episode"),  # title (32-byte slot)
    (0x2a8fc0, 'ワタナベ', 'Watanabe'),                                         # placeholder name (16-byte slot)
    # Internal labels: two resource names and the window-state records' names (64-byte field in each 0x60-byte
    # record; two records share a name, and no data file refers to them, so they are not lookup keys).
    (0x2b7ea0, '一般兵器テクスチャ転送用', 'Weapon texture upload'),
    (0x2bdcc0, '一般兵器リソースファイル', 'Weapon resource file'),
    (0x2c7520, '確認ウィンドウ', 'Confirm window'),
    (0x2c7580, '警告ウィンドウ', 'Warning window'),
    (0x2c75e0, 'YESNOウィンドウ', 'Yes/No window'),
    (0x2c7640, 'YESだけウィンドウ', 'Yes-only window'),
    (0x2c76a0, 'YESだけど警告ウィンドウ', 'Yes-only warning window'),
    (0x2c7700, 'ポーズメニュー', 'Pause menu'),
    (0x2c7760, 'ポーズメニュー', 'Pause menu'),
    (0x2c77c0, '結果メニュー', 'Results menu'),
    (0x2c7820, 'チェック中', 'Checking'),
    (0x2c7880, 'ロード選択', 'Load select'),
    (0x2c78e0, 'ロード中', 'Loading'),
    (0x2c7940, 'ロード成功', 'Load succeeded'),
    (0x2c79a0, 'ロード失敗', 'Load failed'),
    (0x2c7a00, 'セーブ選択', 'Save select'),
    (0x2c7a60, 'セーブ中', 'Saving'),
    (0x2c7ac0, 'セーブ成功', 'Save succeeded'),
    (0x2c7b20, 'セーブ失敗', 'Save failed'),
    (0x2c7b80, 'フォーマット中', 'Formatting'),
    (0x2c7be0, 'フォーマット成功', 'Format succeeded'),
    (0x2c7c40, 'フォーマット失敗', 'Format failed'),
]
ICON_TITLE = ('アナザーセンチュリーズエピソード', 'Ａｎｏｔｈｅｒ　Ｃｅｎｔｕｒｙ’ｓ', 'Ｅｐｉｓｏｄｅ')  # PS2 browser, 2 lines


def patch_elf(elf, report):
    out = bytearray(elf)
    for va, old, new in (ELF_STRINGS[:2] if DIAG.get('no_cleanup') else ELF_STRINGS):
        o = va - 0x100000 + 0x80
        raw = old.encode('cp932')
        require(bytes(out[o:o + len(raw) + 1]) == raw + bytes(1), 'ELF string at %#x differs' % va)
        slot = len(raw) + 1
        while out[o + slot] == 0 and slot < 64:
            slot += 1
        enc = new.encode('cp932')
        require(len(enc) < slot, 'ELF string %r does not fit its %d-byte slot' % (new, slot))
        out[o:o + slot] = enc + bytes(slot - len(enc))
    report['elf_strings'] = [new for _, _, new in ELF_STRINGS]
    return bytes(out)


def patch_icon_sys(data):
    """Memory-card browser title: 68-byte CP932 field at 0xC0, second line starting at the byte offset in 6-7."""
    out = bytearray(data)
    require(out[:4] == b'PS2D' and bytes(out[0xc0:0xc0 + 68]).split(bytes(1))[0].decode('cp932') == ICON_TITLE[0],
            'icon.sys title differs')
    line1, line2 = ICON_TITLE[1].encode('cp932'), ICON_TITLE[2].encode('cp932')
    require(len(line1) + len(line2) < 68, 'icon.sys title too long')
    out[0xc0:0xc0 + 68] = (line1 + line2).ljust(68, bytes(1))
    struct.pack_into('<H', out, 6, len(line1))
    return bytes(out)
MENU_FMG = r'\menu\fmg'
WINDOW_MSG = r'\window\msg'
MENU_TM2 = '\\menu\\tm2\\'
MENU_DIR = '\\menu\\'
WINDOW_BND = r'\window\bnd'
F005_CCM = r'\target\menu\font\tm2\f005.ccm'
ICON_SYS = r'\system\icon.sys'
F005_TM2 = r'\target\menu\font\tm2\f005.tm2'


def patch_dialogue_font(data, ui=None):
    """Fe1p/Fe2p: English set in the dialogue font; with ``ui``, also the rebuilt HUD font (lock-on labels and
    radio speaker names) and the translated text tables nested inside."""
    from dialogue_source import unnamed_bnd
    kids = unnamed_bnd(data)

    def child(ident, size_at):
        o, _ = kids[ident]
        return data[o:o + u32(data, o + size_at)]
    repl = {}
    repl[DIALOGUE_CCM], repl[DIALOGUE_TM2] = patch_font(child(DIALOGUE_CCM, 4), child(DIALOGUE_TM2, 0))
    if ui is None:
        return unnamed_bnd_replace(data, repl)
    if ui.ready.get('hud13'):
        repl[HUD_CCM], repl[HUD_TM2] = patch_small_font(child(HUD_CCM, 4), child(HUD_TM2, 0), 'hud13')
    return ui.unnamed_bnd(data, extra=repl)


def english_briefing(table, rows, report):
    """Japanese fNNN rows -> rows with checked English (mission name, objectives, briefing, debriefing)."""
    path = briefing_layout.DIR / ('f%s.json' % table)
    if not path.exists():
        return None
    tr = json.loads(path.read_text(encoding='utf-8'))
    if tr.get('excluded'):
        return None
    out = dict(rows)
    done = 0
    for r in tr['rows']:
        if not r.get('en'):
            continue
        require(rows.get(r['id']) == r['ja'], 'f%s id %d: Japanese source differs from disc' % (table, r['id']))
        bad = briefing_layout.problems(r)
        require(not bad, 'f%s id %d: %s' % (table, r['id'], bad))
        out[r['id']] = briefing_layout.stored(r['id'], r['en'])
        done += 1
    if not done:
        return None
    report.setdefault('briefing', {})[table] = {'rows_translated': done, 'rows': len(tr['rows'])}
    return out


def english_container(data, mission, report):
    """Append an English main table to a mission text container and redirect word 20 to it."""
    tr = dialogue_layout.load(mission)
    main = u32(data, 20)
    require(main, 'Mission %s has no main table' % mission)
    rows = fmg_read(data[main:main + u32(data, main + 4)])
    win = dialogue_layout.windows(tr['rows'])
    done = 0
    for r in tr['rows']:
        if not r.get('en') or not dialogue_layout.split(r['ja'])[1].strip():
            continue
        keep = DIAG.get('rows', {}).get(mission)
        if keep is not None and (r['id'] in keep[1]) != keep[0]:
            continue                       # diagnostic: row left Japanese
        require(rows.get(r['id']) == r['ja'], 'm%s id %d: Japanese source differs from disc' % (mission, r['id']))
        bad = dialogue_layout.problems(r, win[r['id']])
        require(not bad, 'm%s id %d: %s' % (mission, r['id'], bad))
        rows[r['id']] = dialogue_layout.stored(r['ja'], r['en'], win[r['id']], DIAG.get('scale_typing', False))
        done += 1
    if not done:
        return None
    table = fmg_build(rows)
    out = bytearray(data) + bytes(-len(data) % 16)
    new_main = len(out)
    out += table
    struct.pack_into('<I', out, 20, new_main)
    # The three header lists (words 8/12/16, row counts in bytes 28-30) can also reference the main table
    # (e.g. id 40 in most missions); point those rows at the English table too.
    for n, at in enumerate((u32(data, 8), u32(data, 12), u32(data, 16))):
        for k in range(data[28 + n] if at else 0):
            if u32(out, at + 16 * k + 4) == main:
                struct.pack_into('<I', out, at + 16 * k + 4, new_main)
    struct.pack_into('<I', out, 4, len(out))
    check = fmg_read(bytes(out[new_main:new_main + u32(out, new_main + 4)]))
    require(check == rows, 'Container round trip failed for m' + mission)
    report.setdefault('dialogue', {})[mission] = {'rows_translated': done, 'rows': len(tr['rows']),
                                                  'container_before': len(data), 'container_after': len(out)}
    return bytes(out)


def english_f205(original_rows, report):
    """Japanese f205 rows -> rows with English titles and paginated English pages (ids term*100+n)."""
    rows = dict(original_rows)
    translated_terms = translated_pages = 0
    for term in layout.load():
        t = term['term']
        if term.get('title_en'):
            rows[t] = term['title_en']
        if not term['pages'] or not all(p.get('en') for p in term['pages']):
            continue
        pages = layout.term_pages(term)
        require(len(pages) <= 99, 'Too many pages for term %d' % t)
        # The game probes t*100+1, +2, ... until an id is missing, so the page ids must be exactly 1..len(pages).
        for k in range(1, 100):
            rows.pop(t * 100 + k, None)
        for k, lines in enumerate(pages, 1):
            text = '\n'.join(lines)
            require(layout.game_bytes(text) <= layout.PAGE_BYTES and len(lines) <= layout.PAGE_LINES,
                    'Page %d overflows' % (t * 100 + k))
            rows[t * 100 + k] = layout.stored(text)
        translated_terms += 1
        translated_pages += len(pages)
    report['f205'] = {'terms_translated': translated_terms, 'game_pages': translated_pages,
                      'titles_translated': sum(1 for t in layout.load() if t.get('title_en'))}
    return rows


def patch_font(ccm, tm2):
    f = Font(ccm, tm2)
    add_english(f)
    new_ccm, new_tm2 = f.ccm_bytes(), f.tm2_bytes()
    require(len(new_tm2) == len(tm2), 'Atlas size changed')
    check = Font(new_ccm, new_tm2)
    old = Font(ccm, tm2)
    for code, g in old.map.items():
        if code < 0x80 or 0x824F <= code <= 0x8258:
            continue
        require(check.glyphs[check.map[code]]['raw'] == old.glyphs[g]['raw'], 'Original glyph changed')
    return new_ccm, new_tm2


class DataBin:
    """DATA.BIN read through the source ISO without loading it whole (the tools also run on 32-bit Python)."""

    def __init__(self, stream, offset, size):
        self.f, self.base, self.size = stream, offset, size
        self.f.seek(offset)
        head = self.f.read(64 << 10)
        count = u32(head, 16)
        first = min(u32(head, 32 + i * 16 + 4) for i in range(count))
        self.f.seek(offset)
        self.header = bytearray(self.f.read(first))
        self.entries = bnd_entries(bytes(self.header))

    def read(self, e):
        self.f.seek(self.base + e['offset'])
        return self.f.read(e['size'])


def blank_dead_tables(body, report):
    """Clear the strings of Japanese text tables a mission container no longer references (its main table and
    one-row labels are replaced by appended English copies), so no stale Japanese stays in the image. Pointers and
    headers stay, so a reference the header map missed would show an empty line, not old text."""
    from dialogue_source import container
    from japanese_inventory import tables_in, JP
    main, names = container(body)
    live = {main} | {o for _, o in names}
    out = bytearray(body)
    cleared = 0
    for at, rows in tables_in(body):
        if at in live or not any(v and JP.search(v) for v in rows.values()):
            continue
        size, _, groups, count, table = struct.unpack_from('<5I', body, at + 4)
        for i in range(count):
            p = u32(body, at + table + 4 * i)
            if p:
                end = body.index(b'\0', at + p, at + size)
                out[at + p:end] = bytes(end - at - p)
        cleared += 1
    # Leftover strings from earlier drafts sit in the padding between tables (unreferenced, already on the
    # original disc). Clear a gap when it holds nothing but NUL-terminated text with Japanese.
    spans = sorted((at, at + struct.unpack_from('<I', body, at + 4)[0]) for at, _ in tables_in(body))
    for (_, end), (start, _) in zip(spans, spans[1:]):
        gap = body[end:start]
        parts = [p for p in gap.split(bytes(1)) if p]
        if not parts:
            continue
        try:
            text = [p.decode('cp932') for p in parts]
        except UnicodeDecodeError:
            continue
        if all(t.isprintable() for t in text) and any(JP.search(t) for t in text):
            out[end:start] = bytes(start - end)
            report['padding_text_cleared'] = report.get('padding_text_cleared', 0) + 1
    report['dead_tables_cleared'] = report.get('dead_tables_cleared', 0) + cleared
    return bytes(out)


DIAG = {}     # diagnostic switches from the command line (never used for a release build)


def build_data(db, report):
    """Return (patches {offset: bytes} inside the old DATA.BIN, appended tail bytes, new DATA.BIN size)."""
    entries = db.entries
    changed = {}
    ui = UiText()
    tex = TextureText()
    std = {e['name'].lower(): e for e in entries}
    sccm = std[r'\target\menu\font\tm2\f010.ccm']
    stm2 = std[r'\target\menu\font\tm2\f010.tm2']
    changed[sccm['index']], changed[stm2['index']] = patch_font(db.read(sccm), db.read(stm2))
    sf205 = std[r'\target\menu\fmg\f205.fmg']
    f205_ja = fmg_read(db.read(sf205))
    f205_en = english_f205(f205_ja, report)
    changed[sf205['index']] = fmg_build(f205_en)
    for e in entries:
        m = BRIEFING_TABLE.search(e['name'])
        if m and '\\menu\\fmg\\' in e['name']:
            rows = english_briefing(m.group(1), fmg_read(db.read(e)), report)
            if rows:
                changed[e['index']] = fmg_build(rows)
    # Remaining UI tables (matched by content), standalone copies and window messages.
    for e in entries:
        n = e['name'].lower()
        if e['index'] in changed:
            continue
        if n.endswith('.fmg') and (MENU_FMG in n or WINDOW_MSG in n):
            new = ui.fmg(db.read(e))
        elif WINDOW_BND in n:
            from dialogue_source import unnamed_bnd
            data = db.read(e)
            extra = {}
            for ident, (o, size) in unnamed_bnd(data).items():
                d = data[o:o + size]
                if len(d) >= 64 and u32(d, 8) == 1 and 64 <= u32(d, 0) <= size:
                    t = tex.replace(d[:u32(d, 0)])
                    if t:
                        extra[ident] = t
            new = ui.unnamed_bnd(data, extra=extra)
        elif MENU_TM2 in n and n.endswith('.tm2'):
            new = tex.replace(db.read(e))
        else:
            new = None
        if new:
            changed[e['index']] = new
    if ui.ready.get('f005'):
        c5, t5 = std[F005_CCM], std[F005_TM2]
        changed[c5['index']], changed[t5['index']] = patch_small_font(db.read(c5), db.read(t5), 'f005')
    for name in FONT_BUNDLES:
        e = next(x for x in entries if x['name'].endswith('\\' + name))
        bundle = unpack(db.read(e))
        repl = {}
        repl['f010.ccm'], repl['f010.tm2'] = patch_font(bnd_child(bundle, 'f010.ccm'), bnd_child(bundle, 'f010.tm2'))
        if name in TEXT_BUNDLES:
            require(fmg_read(bnd_child(bundle, 'f205.fmg')) == f205_ja, 'f205 copy differs in ' + name)
            repl['f205.fmg'] = fmg_build(f205_en)
            for child in bnd_entries(bundle):
                m = BRIEFING_TABLE.search(child['name'])
                if m:
                    suffix = '\\fmg\\f%s.fmg' % m.group(1)
                    rows = english_briefing(m.group(1), fmg_read(bnd_child(bundle, suffix)), {})
                    if rows:
                        repl[suffix] = fmg_build(rows)
        for child in bnd_entries(bundle):
            if child['name'].lower().endswith('.fmg') and not any(child['name'].lower().endswith(k.lower()) for k in repl):
                new = ui.fmg(bundle[child['offset']:child['offset'] + child['size']])
                if new:
                    repl[child['name']] = new
        for child in bnd_entries(bundle):
            if child['name'].lower().endswith('.tm2') and child['name'] not in repl:
                t = tex.replace(bundle[child['offset']:child['offset'] + child['size']])
                if t:
                    repl[child['name']] = t
        if ui.ready.get('f005'):
            repl['f005.ccm'], repl['f005.tm2'] = patch_small_font(bnd_child(bundle, 'f005.ccm'), bnd_child(bundle, 'f005.tm2'), 'f005')
        new_plain = bnd_replace(bundle, repl)
        packed = pack(new_plain)
        require(unpack(packed) == new_plain, 'Pack round trip failed for ' + name)
        changed[e['index']] = packed
        report.setdefault('bundles', {})[name] = {'plain_before': len(bundle), 'plain_after': len(new_plain),
                                                 'packed_before': e['size'], 'packed_after': len(packed)}
        print('packed', name, len(packed), 'slot', e['size'])
    for e in entries:
        n = e['name']
        if n.lower().endswith('.csc') and MENU_DIR in n.lower() and not any(n.endswith('\\' + b) for b in FONT_BUNDLES):
            bundle = unpack(db.read(e))
            repl = {}
            for child in bnd_entries(bundle):
                if child['name'].lower().endswith('.tm2'):
                    t = tex.replace(bundle[child['offset']:child['offset'] + child['size']])
                    if t:
                        repl[child['name']] = t
            if repl:
                new_plain = bnd_replace(bundle, repl)
                packed = pack(new_plain)
                require(unpack(packed) == new_plain, 'Pack round trip failed for ' + n)
                changed[e['index']] = packed
    for name in DIALOGUE_FONT_BUNDLES:
        # Each exists twice in DATA.BIN under different resource ids (byte-identical copies); patch all.
        for e in [x for x in entries if x['name'].endswith('\\' + name)]:
            changed[e['index']] = patch_dialogue_font(db.read(e), None if DIAG.get('stock_hud') else ui)
            report.setdefault('dialogue_font', {})['%s#%d' % (name, e['id'])] = {
                'before': e['size'], 'after': len(changed[e['index']])}
    translated = set(dialogue_layout.missions())
    for e in entries:
        m = re.search(r'InGame(\d+)\.bnd$', e['name'])
        if not m:
            continue
        body = db.read(e)
        if m.group(1) in DIAG.get('stock_missions', ()):
            continue
        if m.group(1) in translated and m.group(1) not in DIAG.get('stock_dialogue', ()):
            body = english_container(body, m.group(1), report) or body
        labels = ui.container_labels(body) if u32(body, 0) == 0x100 and m.group(1) not in DIAG.get('stock_labels', ()) else None
        body = labels or body
        if body != db.read(e) and not DIAG.get('no_cleanup') and not DIAG.get('no_blank'):
            body = blank_dead_tables(body, report)
        if body != db.read(e):
            changed[e['index']] = body
    icon = next(x for x in entries if x['name'].lower().endswith(ICON_SYS))
    changed[icon['index']] = patch_icon_sys(db.read(icon))
    report['ui'] = dict(ui.applied)
    report['textures'] = dict(tex.applied)
    report['ui_fonts_rebuilt'] = {k: v for k, v in ui.ready.items() if k != 'f010'}
    # Place resources: in place when they fit the slot, else appended after the old end.
    header = bytearray(db.header)
    starts = sorted(e['offset'] for e in entries) + [db.size]
    patches, tail = {}, bytearray()
    end = align(db.size)
    placed = {}
    for index, body in sorted(changed.items()):
        e = entries[index]
        slot = min(s for s in starts if s > e['offset']) - e['offset']
        if len(body) <= slot:
            patches[e['offset']] = body + bytes(slot - len(body))
            where = e['offset']
        else:
            tail += bytes(align(end + len(tail)) - end - len(tail))
            where = end + len(tail)
            tail += body
            # The old slot is dead once the directory points at the copy; clear it (no stale Japanese in the image)
            # unless another resource shares its bytes.
            if not DIAG.get('no_cleanup') and not any(x['offset'] == e['offset'] and x['index'] not in changed
                                                      for x in entries if x is not e):
                patches[e['offset']] = bytes(slot)
        struct.pack_into('<II', header, 32 + index * 16 + 4, where, len(body))
        placed['%s#%d' % (e['name'], e['id'])] = {'offset': where, 'size': len(body), 'in_place': where == e['offset']}
    if tail:
        tail = bytes(end - db.size) + tail
        tail += bytes(align(len(tail)) - len(tail))
    new_size = db.size + len(tail)
    struct.pack_into('<I', header, 12, new_size)
    patches[0] = bytes(header)
    report['placed'] = placed
    report['changed'] = {str(i): hashlib.sha256(b).hexdigest() for i, b in changed.items()}
    return patches, bytes(tail), new_size, changed


def directory_records(prefix, lba, size):
    at = lba * SECTOR
    end = at + size
    while at < end:
        length = prefix[at]
        if not length:
            at = (at // SECTOR + 1) * SECTOR
            continue
        yield at, bytes(prefix[at:at + length])
        at += length


def write_data_bin(src, dst, old, patches, tail):
    """Stream the original DATA.BIN to ``dst`` with in-place patches applied, then the appended tail."""
    edits = sorted(patches.items())
    pos = 0
    for at, body in edits + [(old['size'], b'')]:
        require(at >= pos, 'Overlapping DATA.BIN patches')
        src.seek(old['offset'] + pos)
        left = at - pos
        while left:
            block = src.read(min(8 << 20, left))
            dst.write(block)
            left -= len(block)
        dst.write(body)
        pos = at + len(body)
    dst.write(tail)


def write_iso(patches, tail, new_size, changed_payloads, out_path, report, other_files=None):
    with open(SOURCE_ISO, 'rb') as src:
        files = iso_files(src)
    order = sorted(files, key=lambda k: files[k]['offset'])
    sizes = {k: files[k]['size'] for k in files}
    sizes['/DATA.BIN'] = new_size
    wanted, shift = {}, 0
    for name in order:
        wanted[name] = {'offset': files[name]['offset'] + shift, 'size': sizes[name]}
        shift += align(sizes[name]) - align(files[name]['size'])
    total = SOURCE_ISO.stat().st_size
    old_end = align(max(r['offset'] + r['size'] for r in files.values()))
    new_end = align(max(r['offset'] + r['size'] for r in wanted.values()))
    require(new_end <= total - 257 * SECTOR, 'Growth exceeds the disc padding (%d bytes)' % (new_end - old_end))
    prefix_end = min(r['offset'] for r in files.values())
    with open(SOURCE_ISO, 'rb') as src:
        prefix = bytearray(src.read(prefix_end))
    # ISO9660 directory records (both byte orders).
    patched = set()

    def walk(lba, size, path):
        for at, rec in directory_records(prefix, lba, size):
            name = rec[33:33 + rec[32]]
            if name in (b'\0', b'\1'):
                continue
            full = path + '/' + name.decode('ascii').split(';')[0]
            if rec[25] & 2:
                walk(u32(rec, 2), u32(rec, 10), full)
                continue
            w = wanted[full]
            for delta, value in ((2, w['offset'] // SECTOR), (10, w['size'])):
                struct.pack_into('<I', prefix, at + delta, value)
                struct.pack_into('>I', prefix, at + delta + 4, value)
            patched.add(full)
    walk(u32(prefix, 16 * SECTOR + 158), u32(prefix, 16 * SECTOR + 166), '')
    require(patched == set(wanted), 'Incomplete ISO9660 update')
    # UDF file entries.
    udf = pycdlib.PyCdlib()
    udf.open(str(SOURCE_ISO))
    partition = udf.udf_main_descs.partitions[0].part_start_location
    count = 0
    for parent, _, names in udf.walk(udf_path='/'):
        for name in names:
            path = parent.rstrip('/') + '/' + name
            w = wanted[path.upper()]
            entry = udf.get_record(udf_path=path)
            start = entry.orig_extent_loc * SECTOR
            fe = bytearray(prefix[start:start + SECTOR])
            require(struct.unpack_from('<H', fe)[0] == 261, 'Expected a UDF file entry')
            ad = 176 + u32(fe, 168)
            require(u32(fe, 172) == 8, 'Expected one short allocation descriptor')
            struct.pack_into('<Q', fe, 56, w['size'])
            struct.pack_into('<Q', fe, 64, align(w['size']) // SECTOR)
            struct.pack_into('<II', fe, ad, w['size'], w['offset'] // SECTOR - partition)
            fix_udf_tag(fe)
            prefix[start:start + SECTOR] = fe
            count += 1
    udf.close()
    require(count == len(wanted), 'Incomplete UDF update')
    tmp = out_path.with_suffix('.partial')
    with open(SOURCE_ISO, 'rb') as src, open(tmp, 'wb') as dst:
        dst.write(prefix)
        for name in order:
            w = wanted[name]
            dst.write(bytes(w['offset'] - dst.tell()))
            if name == '/DATA.BIN':
                write_data_bin(src, dst, files[name], patches, tail)
                require(dst.tell() == w['offset'] + new_size, 'DATA.BIN size mismatch')
            elif other_files and name in other_files and isinstance(other_files[name], Path):
                # A rebuilt file on disk (the movies): streamed, same size.
                require(other_files[name].stat().st_size == files[name]['size'], 'Replacement for %s changes its size' % name)
                with open(other_files[name], 'rb') as rf:
                    shutil.copyfileobj(rf, dst, 8 << 20)
            elif other_files and name in other_files:
                require(len(other_files[name]) == files[name]['size'], 'Replacement for %s changes its size' % name)
                dst.write(other_files[name])
            else:
                src.seek(files[name]['offset'])
                left = files[name]['size']
                while left:
                    block = src.read(min(8 << 20, left))
                    dst.write(block)
                    left -= len(block)
        dst.write(bytes(new_end - dst.tell()))
        src.seek(new_end)  # remaining padding and the trailing UDF anchor, unchanged
        shutil.copyfileobj(src, dst, 8 << 20)
    require(tmp.stat().st_size == total, 'Image size changed')
    tmp.replace(out_path)
    # Verify: extents as planned and payloads equal.
    with open(out_path, 'rb') as f:
        got = iso_files(f)
        require(got == wanted, 'Output extents differ from plan')
        base = wanted['/DATA.BIN']['offset']
        f.seek(base)
        db = DataBin(f, base, new_size)
        for e in db.entries:
            if str(e['index']) in changed_payloads:
                require(hashlib.sha256(db.read(e)).hexdigest() == changed_payloads[str(e['index'])],
                        'Changed resource differs on disc: ' + e['name'])
        # Files streamed from disk (the movies) must be on the disc byte for byte.
        for name, src_path in (other_files or {}).items():
            if isinstance(src_path, Path):
                f.seek(wanted[name]['offset'])
                h, left = hashlib.sha256(), wanted[name]['size']
                while left:
                    block = f.read(min(left, 8 << 20))
                    h.update(block)
                    left -= len(block)
                require(h.hexdigest() == sha256(src_path), 'Rebuilt file differs on disc: ' + name)
        # Spot-check untouched resources against the source disc.
        with open(SOURCE_ISO, 'rb') as s:
            sdb = DataBin(s, files['/DATA.BIN']['offset'], files['/DATA.BIN']['size'])
            for e in db.entries[::97]:
                if str(e['index']) not in changed_payloads:
                    require(db.read(e) == sdb.read(sdb.entries[e['index']]), 'Untouched resource differs: ' + e['name'])
    check = pycdlib.PyCdlib()
    check.open(str(out_path))
    for parent, _, names in check.walk(udf_path='/'):
        for name in names:
            path = parent.rstrip('/') + '/' + name
            entry = check.get_record(udf_path=path)
            w = wanted[path.upper()]
            require(entry.info_len == w['size'] and
                    (partition + entry.alloc_descs[0].log_block_num) * SECTOR == w['offset'], 'UDF/ISO mismatch ' + path)
    check.close()
    report['iso'] = {'moved_files': sum(1 for k in files if wanted[k]['offset'] != files[k]['offset']),
                     'data_bin_growth': new_size - files['/DATA.BIN']['size'], 'size': total}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('version')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--movies', default=None, help='comma list of movie specs to include (default: all with a spec)')
    ap.add_argument('--no-lyrics', action='store_true',
                    help='public release: movies without the user-supplied song lyrics (karaoke left out)')
    ap.add_argument('--stock-missions', default='', help='diagnostic: comma list of mission numbers (e.g. 001) left untranslated')
    ap.add_argument('--stock-hud', action='store_true', help='diagnostic: keep the stock HUD font and Fe speaker tables')
    ap.add_argument('--stock-dialogue', default='', help='diagnostic: missions whose dialogue table stays stock')
    ap.add_argument('--stock-labels', default='', help='diagnostic: missions whose lock-on label tables stay stock')
    ap.add_argument('--no-blank', action='store_true', help='diagnostic: do not blank unused mission tables')
    ap.add_argument('--scale-typing', action='store_true', help='diagnostic: English typed as fast as the Japanese took')
    ap.add_argument('--rows', default='', help='diagnostic: MISSION:A-B[,C-D] translates only those rows; MISSION:!A-B all but those')
    ap.add_argument('--no-cleanup', action='store_true',
                    help='diagnostic: stock ELF labels, no blanking of unused tables, no zeroing of moved slots')
    a = ap.parse_args()
    report = {'version': a.version}
    if a.stock_missions:
        DIAG['stock_missions'] = set(a.stock_missions.split(','))
    if a.stock_hud:
        DIAG['stock_hud'] = True
    if a.no_cleanup:
        DIAG['no_cleanup'] = True
    if a.stock_dialogue:
        DIAG['stock_dialogue'] = set(a.stock_dialogue.split(','))
    if a.stock_labels:
        DIAG['stock_labels'] = set(a.stock_labels.split(','))
    if a.no_blank:
        DIAG['no_blank'] = True
    if a.scale_typing:
        DIAG['scale_typing'] = True
    if a.rows:
        mission, spec = a.rows.split(':')
        include = not spec.startswith('!')
        ids = set()
        for part in spec.lstrip('!').split(','):
            lo, _, hi = part.partition('-')
            ids |= set(range(int(lo), int(hi or lo) + 1))
        DIAG['rows'] = {mission: (include, ids)}
    if DIAG:
        report['diagnostic'] = {k: sorted(v) if isinstance(v, set) else str(v) for k, v in DIAG.items()}
    with open(SOURCE_ISO, 'rb') as f:
        rec = iso_files(f)['/DATA.BIN']
        patches, tail, new_size, _ = build_data(DataBin(f, rec['offset'], rec['size']), report)
    report['data_bin'] = {'before': rec['size'], 'after': new_size}
    print(json.dumps({k: v for k, v in report.items() if k not in ('placed', 'changed')}, indent=1))
    print('placed:', {k.split('\\')[-1]: ('in place' if v['in_place'] else 'appended') for k, v in report['placed'].items()})
    if not a.write:
        print('DRY RUN - nothing written')
        return
    out = ROOT / 'work/output' / ('ACE-EN-%s.iso' % a.version)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(SOURCE_ISO, 'rb') as f:
        rec = iso_files(f)['/SLPS_253.94']
        f.seek(rec['offset'])
        elf = patch_elf(f.read(rec['size']), report)
    import movie_text
    only = set(a.movies.split(',')) if a.movies else None
    movies = {} if DIAG else movie_text.ready(only, a.no_lyrics)      # diagnostic builds keep the stock movies
    report['movies_without_lyrics'] = bool(a.no_lyrics)
    report['movies'] = {name: json.loads((path.with_suffix('.json')).read_text(encoding='utf-8'))['sha256']
                        for name, path in movies.items()}
    write_iso(patches, tail, new_size, report['changed'], out, report, dict({'/SLPS_253.94': elf}, **movies))
    report['sha256'] = sha256(out)
    report['source_sha256'] = sha256(SOURCE_ISO)
    (out.with_suffix('.json')).write_text(json.dumps(report, indent=1), encoding='utf-8')
    print(json.dumps(report['iso']), report['sha256'])
    print('wrote', out)


if __name__ == '__main__':
    main()
