# HUD warning restoration (0.1.19)

The user reported question marks in the out-of-bounds warning on 2026-10-16 and requested the original
`AREA OVER` label. The original text is already English, stored with full-width CP932 letters and a full-width
space. It is row 2 of child `50140/5` in both `Fe1p.bnd` and `Fe2p.bnd`. The same table contains `CAUTION`,
`ON AIR`, `MISSILE`, and `ERROR` in rows 22-25.

These rows contain no Japanese kana/kanji, so the translation inventory correctly leaves them alone. However,
the HUD font rebuild previously retained only characters used by translation groups. It discarded these
full-width English glyphs and pointed their codes at `?`, including the space. A zero-Japanese inventory is
therefore insufficient to verify existing English labels.

`tools/ui_layout.py` now includes the five stock labels in the HUD font's retained character set. The font
builder repacks their original pixels and retains their screen metrics. Their strings, warning panel,
placement, trigger logic and timing are unchanged. Both one-player and two-player HUD fonts receive the fix.

## Verification

`python tools/verify_hud_warning.py` checks the proposed rebuild before writing an ISO. It verifies the actual
stock table contents, exact stock warning glyph pixels and metrics, palette entries, and unchanged ASCII
glyphs compared with 0.1.18. Add `--write` to save reconstructed font previews under
`work/ui/hud-warning-0.1.19/`. These are font proofs, not emulator screenshots.

Run `python tools/build.py 0.1.19 --movies MOVIE001,MOVIE002,MOVIE003` for the full dry run, then add `--write`.
Run `python tools/verify_hud_warning.py work/output/ACE-EN-0.1.19.iso --write` to verify both on-disc fonts and
compare every DATA.BIN resource with 0.1.18. Only the HUD CCM/TM2 font children in `Fe1p.bnd` and `Fe2p.bnd`
may change; the executable must remain identical. Run the usual Japanese inventory afterward.

The reconstructed warning uses the original game's typeface. Fresh-boot, in-game confirmation remains for
user testing. This is a local test build; no release was requested.

## Build results

- Output: `work/output/ACE-EN-0.1.19.iso`, 3,357,147,136 bytes.
- SHA-256: `0cae3a989e87bb8b2fabb61bc058d185b2bfcb9a964fead4e8b0b0a6e28a232f`.
- Full dry run and write succeeded, including ISO/UDF layout and on-disc payload hash checks.
- Movie hashes match 0.1.18.
- The on-disc comparison passed: only HUD font children changed, with exact stock warning glyphs and
  unchanged ASCII glyphs. Other DATA.BIN resources, all warning text tables, and the executable are identical.
- The final Japanese inventory found 0 tables and 0 rows.
