# In-mission dialogue

## Where the text is

`\target\fe\InGame\bnd\InGameNNN.bnd`, one container per mission (001-050 with gaps, 080/081 extra missions,
090 and test containers 125/970/971/998/999). 3,493 rows in total (`tools/dialogue_source.py` exports them to
`work/source/dialogue_ja.json`).

Container header, as read by the message-system initializer (EE `0x2363b0`):

| Offset | Meaning |
| --- | --- |
| 0 | 0x100 |
| 4 | total size |
| 8, 12, 16 | three lists of 16-byte rows `(unit id, FMG offset, 0, 0)`: lock-on name tables |
| 20 | **main table**: objectives (ids 1-9) and dialogue (ids 10+) |
| 24 | optional second table |
| 28-30 | row counts of the three lists (the initializer only tests them for non-zero) |

The build appends an English copy of the main table and redirects word 20 (the method ACE 3 used). The original
table stays in the file, unreferenced.

## Control tokens

Registered by the initializer (handler addresses in parentheses): `op` (0x237090) and `ed` (0x2370c0) open and
close a radio exchange; `sp(n)` typing speed; `w`; `ab(n)` wait n ms then advance (`ab(0)` continues straight
into the next row); `cs`/`ce`; `on`/`off` window on/off; `fz`.

Tokens only ever appear before or after the visible text (checked on all 3,493 rows). Translators therefore write
plain English, and `dialogue_layout.stored` puts the original prefix and suffix tokens back.

## Limits

* **Main radio window: 93 visible bytes per row** (proven in play; the Japanese maximum is 83). The code below allows
  128, but the operator window crashed on a buffer that is not this one. **Typing buffer (code):** The typewriter (EE 0x237af8-0x237b28) appends each character to a
  132-byte buffer at message+0x24, with the length at message+0xa8 and **no bounds check**: an overflow would
  corrupt the length and pointer fields. The message start routine (0x2366e0) clears the 0xf0-byte message
  object for every row, so the limit is per row. Tokens are not copied; `#c[RRGGBB]` codes and line breaks are.
  Japanese rows top out near 90 visible bytes.
* **Lines: 2** in the main radio window (no Japanese row uses more). **Operator window** (rows from `<op()>` to
  `<ed()>`): **1 line and at most 54 bytes**, or **46 bytes** for rows with a `<cs(n)>` speaker colour (the colour code
  shares the buffer; a 53-byte enemy line stalled mission 3's script so the last enemy could not retreat). A two-line message froze the game and a 57-byte one crashed it in
  play; the Japanese never exceeds one line or 52 bytes there.
* **Objective / failure labels** (rows 1-9 without tokens, drawn on the HUD): at most 28 bytes, the Japanese
  maximum (buffer not located).
* **Width: 400 units** in the dialogue font (widest Japanese line 408; nearly all at or below 383).

## Font

Dialogue and objectives are drawn with resource 50070 (CCM, 18-unit cell, 1,087 glyphs) and atlas 50050
(1024x512 PSMT4, uploaded GS-swizzled; `ace_formats` converts it) inside `\target\fe\InGame\param\Fe1p.bnd` and
`Fe2p.bnd` (split screen). Both use the unnamed BND variant. The 13-unit font 50071 (8-bit) draws the lock-on unit
labels only (katakana and fullwidth capitals); those labels are not translated yet.

English glyphs are added as for the menu font (see `vwf.md`) but at **2 texels per unit**. The atlas has about 130
free rows, and 3x or 4x does not fit while every Japanese glyph is kept; untranslated missions still need those
glyphs. Once all dialogue is English, the unused Japanese glyphs can be reclaimed and the set raised to 4x.

## Speakers

Rows carry no speaker. Translators infer the speaker from context and record it in a `speaker` field
(`?` when the scene does not settle it). Finding the mission-script call that selects the portrait is open
research; it would allow speaker names to be checked mechanically.

## Workflow

1. `python tools/dialogue_prepare.py NNN ...` creates `work/translation/en/dialogue/mNNN.json` with the
   briefing table and akurasu flow-chart entry as context.
2. Translate `rows[].en` (visible text only) and `rows[].speaker`.
3. `python tools/dialogue_layout.py check [NNN ...]`; `... preview NNN` renders proofs to `work/ui/dialogue/`.
4. `python tools/build.py <version> --write`.

## Briefings and debriefings

Menu tables `f001`-`f081` (one per mission; MenuCampaign, MenuFree and standalone copies are identical) hold
the mission name (id 1), objective labels (2-4), briefing (100+), debriefing (200+) and failure line (300).
They use the menu font f010 (HD VWF) and the same tokenizer engine with their own handler set (`pic`, `mk`, `ar`,
`pt`, `cs`/`ce`; registration at EE 0x1fd04c). Tokens sit inside sentences, so translators keep the exact
token sequence; `tools/briefing_layout.py` wraps visible text only and rejects any change to the sequence.
Workflow: `tools/briefing_prepare.py`, then translate `work/translation/en/briefing/fNNN.json`, then
`python tools/briefing_layout.py check`. Brief: `docs/briefing_translator_brief.md`.
