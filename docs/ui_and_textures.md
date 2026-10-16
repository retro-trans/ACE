# Menus, HUD and baked-in lettering

## Finding the remaining Japanese

`tools/japanese_inventory.py <iso>` lists every FMG text table still containing Japanese in an image. It scans
plain, packed and nested resources and counts only the tables a mission container's header references (built
images keep the old dialogue tables in place, unreferenced). From 0.1.6 it finds no Japanese text table.

Textures were audited separately (`tools/texture_audit.py`: contact sheets of all 414 distinct menu/system
textures, plus an embedded-texture scan of every other container). Baked Japanese occurs only in about 30 menu
textures, the pause and memory-card window textures and the title screen's copyright lines (relettered with the
companies' English names). The other 2,634 embedded textures (maps, character models, effects) were all viewed
on contact sheets (`work/ui/textures/audit/`): none carries Japanese (a few have English markings such as "KEEP
OUT" or "READY"). The FMV movies are covered in `docs/movies.md`.

Built images also hold no stale Japanese: the build clears the strings of the mission containers' old tables
(no longer referenced once the English copies are appended) and zeroes the old DATA.BIN slot of every resource it
moves, so the inventory scans every table, referenced or not.

## UI text tables (tools/ui_prepare.py, ui_layout.py, ui_apply.py)

The remaining tables are grouped (`work/translation/en/ui/*.json`) by the font that draws them. The stock fonts
are subsets holding exactly the characters their text needs, so glyph coverage identifies the font:

| Group | Font | Content |
| --- | --- | --- |
| weapons (f252, plus unused f206), units (f201/f251), parts (f250) | f005 | hangar names |
| memcard (+2 variants), help (+variant), desc (+variant), modes, common | f010 | menus and dialogs |
| speakers (Fe1p/Fe2p nested table), lockon (one-row tables in InGameNNN) | HUD 50071 | radio names, lock-on |

Limits per group (lines, width, bytes) are the Japanese maxima. The build matches tables **by content** (exact
id and Japanese row set), so every copy of a table is translated wherever it lives. One-row lock-on tables match
per label and are appended to their container, with every list row repointed.

### Rebuilt small fonts

f005 (256x256) and the HUD font 50071 (256x128 PSMT4HH, linear upload, handled like PSMT4) were full, but
everything they draw is now English. `vwf_font.reclaim` repacks each atlas with only the stock glyphs the English
still uses, adds the English set (f005 at 2x, the HUD font at 1x) and points every other code at '?'. A small
font is rebuilt only when all rows of its groups are translated.

From 0.1.19 the HUD retained set also includes the original full-width English labels in Fe1p/Fe2p child
`50140/5`: `AREA OVER`, `CAUTION`, `ON AIR`, `MISSILE`, and `ERROR`. These are not translation groups and
contain no kana/kanji, so a zero-Japanese inventory does not check them. Discarding their glyphs had turned
them into question marks. `tools/verify_hud_warning.py` checks their original pixels/metrics and unchanged
ASCII glyphs; see `docs/hud_warning_0.1.19.md`.

## Executable and save icon

Same-size edits: the title string at EE 0x2c6470 becomes "Another Century's Episode" and the placeholder name
ワタナベ at 0x2a8fc0 becomes "Watanabe". The memory-card browser title in `icon.sys` becomes fullwidth
"Ａｎｏｔｈｅｒ　Ｃｅｎｔｕｒｙ’ｓ / Ｅｐｉｓｏｄｅ". The executable's other Japanese strings are internal labels:
two resource names and the names of the 20 window-state records (64-byte name fields in 0x60-byte records). No
data file refers to them, and two records share a name, so they are not lookup keys. They are written in English
in place (Confirm window, Pause menu, Load succeeded, ...). The 12 remaining Shift-JIS-looking byte runs in the
executable were each inspected: they lie inside MIPS instruction words (lui/ori sequences) or float and double
constant tables (1.0, -1.0, -1.2, ...), not text.

## Baked-in lettering (tools/texture_text.py, texture_apply.py)

Per texture, `work/translation/en/textures/<name>.json` lists label boxes. The tool erases each label by
interpolating the background across the box and draws English (Noto Sans JP, fixed baseline band per box height,
1 px drop shadow, condensed to 70 percent before shrinking). The baseline band splits its spare height evenly
above the capitals and below the baseline, so descenders fit. It then maps the image back onto the texture's own
palette, comparing colours premultiplied by alpha (faint edges on transparent backgrounds stay faint), so size,
format and palette are unchanged.

Spec options beyond the box: `align`, `grow`, `vertical` (with `upward` for labels that read bottom to top, as
all vertical Japanese in these menus does), `height`, `color`, and erase-only labels (`"en": " "`) that clear an
area without lettering. 35 textures are relettered (249 labels). The build replaces every texture whose original bytes match
a spec, in all menu bundles (including the 43 MenuBrief bundles), the standalone files and the window bundles.
Brief: `docs/texture_translator_brief.md`.
