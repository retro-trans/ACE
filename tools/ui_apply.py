"""Apply the UI translation groups (work/translation/en/ui/*.json) to any text table on the disc, by content.

A table is translated when its Japanese rows are exactly one group's rows (same ids and text), so every copy of
a table - menu bundles, standalone files, nested HUD bundles, window bundles - gets the same English without
tracking locations. One-row lock-on label tables in mission containers are matched per label (group 'lockon').

Fonts: the small fonts f005 (names) and the HUD font 50071 are rebuilt (stock glyphs needed by translated text
and existing full-width English HUD labels, plus the English set; every other code shows '?'). A font is rebuilt
and its tables translated only when every row of every group drawn with it has English.
HUD lettering uses an expanded 512x512 atlas at 4x density; see hud_font_hd.py for the runtime caveat.
"""
import collections
import re
import struct
import ui_layout as ul
from ace_formats import Font, fmg_build, fmg_read, require, u32
from vwf_font import add_english, reclaim

JP = re.compile(r'[぀-ヿ一-鿿]')
MAGIC = bytes([0, 0, 1, 0])


class UiText:
    def __init__(self):
        self.groups = {}
        self.lockon = {}
        self.applied = collections.Counter()
        self.ready = {}
        datas = [ul.load(g) for g in ul.groups()]
        for font in {d['font'] for d in datas}:
            self.ready[font] = all(r.get('en') for d in datas if d['font'] == font for r in d['rows'])
        for d in datas:
            if not self.ready[d['font']] and d['font'] != 'f010':
                continue  # a rebuilt small font would turn the untranslated rows into '?'
            if d['group'] == 'lockon':
                for r in d['rows']:
                    if r.get('en'):
                        bad = ul.problems(d, r)
                        require(not bad, 'lockon %r: %s' % (r['ja'], bad))
                        self.lockon[r['ja']] = ul.stored(d, r)
                continue
            self.groups[frozenset((r['id'], r['ja']) for r in d['rows'])] = d

    def translate(self, rows):
        jp = {i: v for i, v in rows.items() if v and JP.search(v)}
        if not jp:
            return None
        out = dict(rows)
        done = 0
        g = self.groups.get(frozenset(jp.items()))
        if g:
            for r in g['rows']:
                if r.get('en'):
                    bad = ul.problems(g, r)
                    require(not bad, '%s id %s: %s' % (g['group'], r['id'], bad))
                    out[r['id']] = ul.stored(g, r)
                    done += 1
            if done:
                self.applied[g['group']] += 1
        elif len(jp) == 1:
            (i, v), = jp.items()
            if v in self.lockon:
                out[i] = self.lockon[v]
                done = 1
                self.applied['lockon'] += 1
        return out if done else None

    def fmg(self, data):
        """New FMG bytes for a table, or None if nothing to translate."""
        rows = fmg_read(data)
        new = self.translate(rows)
        return fmg_build(new) if new else None

    def unnamed_bnd(self, data, extra=None):
        """Translate FMG children (recursively through nested unnamed BNDs); ``extra`` adds replacements."""
        from dialogue_source import unnamed_bnd
        from build import unnamed_bnd_replace
        repl = dict(extra or {})
        for ident, (o, n) in unnamed_bnd(data).items():
            if ident in repl:
                continue
            body = data[o:o + n]
            if body[:4] == MAGIC and 28 <= u32(body, 4) <= n:
                try:
                    new = self.fmg(body[:u32(body, 4)])
                except Exception:
                    new = None
            elif body[:4] == b'BND' + bytes(1) and u32(body, 4) != 0xffff and u32(body, 4) <= n:
                new = self.unnamed_bnd(body[:u32(body, 4)])
            else:
                new = None
            if new:
                repl[ident] = new
        return unnamed_bnd_replace(data, repl) if repl else None

    def container_labels(self, data):
        """Translate the one-row label tables of a mission container (append + repoint every reference)."""
        out = bytearray(data)
        refs = collections.defaultdict(list)
        for n, at in enumerate((u32(data, 8), u32(data, 12), u32(data, 16))):
            for k in range(data[28 + n] if at else 0):
                refs[u32(data, at + 16 * k + 4)].append(at + 16 * k + 4)
        if u32(data, 24):
            refs[u32(data, 24)].append(24)
        changed = False
        for off, slots in sorted(refs.items()):
            if off == u32(data, 20) or data[off:off + 4] != MAGIC:
                continue
            new = self.fmg(data[off:off + u32(data, off + 4)])
            if not new:
                continue
            out += bytes(-len(out) % 16)
            at = len(out)
            out += new
            for slot in slots:
                struct.pack_into('<I', out, slot, at)
            changed = True
        if not changed:
            return None
        struct.pack_into('<I', out, 4, len(out))
        return bytes(out)


def patch_small_font(ccm, tm2, name):
    """Rebuild a small font (f005 or the HUD font) with the English set; see the module docstring."""
    if name == 'hud13':
        from hud_font_hd import rebuild
        new_ccm, new_tm2, _ = rebuild(ccm, tm2, ul.keep_chars(name))
        return new_ccm, new_tm2
    f = Font(ccm, tm2)
    start = reclaim(f, ul.keep_chars(name))
    add_english(f, start=start)
    from english_fonts import compact
    compact(f)
    new_ccm, new_tm2 = f.ccm_bytes(), f.tm2_bytes()
    require(len(new_tm2) == len(tm2) and new_tm2[:32] == tm2[:32], 'Small-font atlas header/size changed')
    check = Font(new_ccm, new_tm2)
    require(all(check.glyph(chr(c)) is not None for c in range(0x20, 0x7f)), 'ASCII coverage incomplete')
    return new_ccm, new_tm2
