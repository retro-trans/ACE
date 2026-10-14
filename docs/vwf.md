# Variable-width font (VWF)

## Finding: the renderer is already proportional

Menu text is drawn from CCM glyph maps paired with TM2 atlases (`\target\menu\font\tm2\f0NN.ccm/.tm2`, also
embedded in each `Menu*.csc` bundle). Every glyph record carries its own metrics:

| Bytes | Field |
| --- | --- |
| 0-15 | `u0 v0 u1 v1` atlas rectangle (float, normalized) |
| 16-17 | bearing (int16) |
| 18-19 | width in atlas pixels |
| 20-21 | advance |
| 22-23 | 0 |

Japanese glyphs already use different advances (あ 18, ！ 4, 。 11 in the 22-unit font), so no executable change
is needed for proportional text. What the stock fonts lack is a usable Latin set: f010 has only the letters needed
for "PlayStation", plus fullwidth Ａ-Ｚ drawn at 13-16 units. With those, English would cost about 12-13 units per
letter.

## Font slots

The widget allocator (EE `0x20ffe0`) chooses the font from the layout descriptor (`desc+8`):

| desc+8 | Font | Cell | Used for |
| --- | --- | --- | --- |
| 0 | f010 | 22 | descriptions, briefings, Terminology, dialogs, most menu text |
| 1 | f005 | 17 | unit and weapon names in the hangar |
| 2 | f001 | 18 | button help (㊤㊦ SELECT ① OK) |
| 3 | f015 | 24 | large digits |

There are no other CCM fonts on the disc (in-mission text uses a separate system). f010 is identical in the
standalone resource and six bundles; MenuTitle carries a 1,228-glyph variant. All eight copies are patched.

## How the renderer draws a glyph (EE 0x1c8bd8-0x1c8ce8)

For each character: pen += bearing x scale; draw a sprite from (pen, y) to (pen + width x scale,
y + cell x scale) with texture coordinates taken from the glyph's float UV rectangle; pen += advance x scale.
So:

* The on-screen size of a glyph depends only on its metrics, never on how many texels its UV rectangle covers.
  This is what makes the HD glyphs possible.
* The pen moves by bearing + advance. Text widths are measured that way (`Font.advance`).

## What the patch does (tools/vwf_font.py)

* Rasterizes printable ASCII (0x20-0x7E) from **Noto Sans JP** (SIL OFL 1.1) at weight 340, 17.5 units,
  squeezed horizontally to 94 percent. The baseline sits on row 18 of the 22-unit cell, matching the stock
  Latin glyphs.
* **HD (since 0.1.1): stored at 4 texels per unit** (glyph cells 88 texels high), rendered with a further 4x
  supersampling. Metrics stay in screen units, so line widths and pages are identical to a 1x design. With an
  emulator at 4x native resolution, every screen pixel of English text maps to its own texel.
* Fills the 11 unused CLUT entries (5-15) with extra alpha levels (4, 8, 16, 24, 40, 48, 56, 75, 85, 107, 117).
  Together with the stock 0/32/64/96/128 this gives a 16-step anti-aliasing ramp. Entries 0-4 are unchanged
  (checked).
* Packs the 95 HD glyphs, with 2 empty texels around each so bilinear sampling never bleeds into a neighbour,
  into atlas rows 576-934 (of 1024; the stock glyphs end at row 574 in all eight copies). The tool refuses to
  write over any non-empty texel.
* Appends 95 glyph records and remaps the ASCII codes to them. `j` gets a negative bearing (-1) instead of
  being clipped, and its stored advance compensates. Original glyph records and texels are kept byte for byte
  (checked by `tools/build.py`).
* Also remaps fullwidth ０-９ to the new digits. The widget copy routine (EE `0x212040`) replaces every ASCII
  digit with its fullwidth CP932 code from the table at `0x2c4c70`, so without this remap English digits would
  render with the old wide glyphs.

Average English advance is about 8 units, so a 440-unit line holds about 54 characters.

Proofs (`python tools/vwf_font.py --preview`, in `work/ui/vwf/`):
`f010_english_hd_4x.png` (as seen at 4x internal resolution), `f010_english_native_1x.png` (native resolution,
one bilinear sample per pixel as the GS does, enlarged for viewing), `f010_atlas_hd_rows.png`.

At native resolution (a real PS2, or an emulator at 1x) each pixel samples one point of the 4x texture. The
text stays readable in the simulation, with slightly uneven stroke weight compared with a dedicated 1x font.

## Not yet done

* f005 (unit and weapon names, 256x256 atlas) has only about 59 free rows: not enough even for a 1x set, let
  alone 4x. An HD set there means reclaiming Japanese-only glyphs once those names are translated, as ACE 3 did.
* f001 is 8-bit (PSMT8) with a different palette; the generator currently supports PSMT4 only.
* In-game verification is pending: fonts were checked offline against the game's metrics.
