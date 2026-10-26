# Shared HUD font refresh (0.1.31)

Follow-up: pow reported a mission-start hang in this build. The saved state
proves a separate operator drawing-buffer overflow (53 glyphs into a 50-glyph
allocation), corrected in 0.1.32. See `docs/dialogue_buffer_0.1.32.md`. The
frame-refresh change is retained; its gameplay/performance confirmation remains
pending. The saved hang alone does not implicate the refresh branches.

On 2026-10-26 pow supplied a screenshot of scrambled red/orange warning banners
and confirmed a fresh boot of local 0.1.30. Its two corrected startup transfers
were necessary but insufficient. No desktop or emulator was controlled.

## Lifetime mismatch

The stock HUD texture occupied the persistent PSMT4HH slot at 0x0c00. Since
0.1.29 it shares the 1024x512 PSMT4 dialogue atlas at 0x2600. This is a reused
GS region, not permanent font storage. The executable also uses 0x2600 in its
texture save/restore machinery (EE 0x141228/0x141280, 0x1412a4/0x1412a8 and
0x1418f8/0x1418fc); the latter path builds restoration packets through
0x16a4e0 -> 0x16c1f0 -> 0x1f51b0.

The HUD preparation routines contain these existing dialogue uploads:

| Mode | Upload path | Quiet-frame skip branch |
| --- | --- | --- |
| 1P | 0x1e1ad8 -> 0x17d030, using descriptor prepared by 0x17d4d0 | 0x1e1ac8 -> 0x1e1ae0 |
| 2P | 0x1e1b70 -> 0x17d1d0 | 0x1e1b58 -> 0x1e1b78 |

Without dialogue (and without the 1P status flag), both paths skip the refresh.
The original HUD could rely on its separate persistent slot; the shared font
cannot. Warning banners and lock-on names can be drawn during these quiet
frames and sample stale data in the shared allocation.

## Correction

Replace the two skip branches with NOPs only when the shared font is enabled.
Keep the existing setup, transfer order, synchronization, resource-null guards
and palettes. The 1P flag/dialogue queries still execute with their original
side effects. The 2P font lookup still uses its original null guard.
The two startup corrections from 0.1.30 remain.

The atlas, glyph maps, metrics, Japanese glyph cleanup, translated dialogue,
movies and both songs are unchanged. The font refresh adds a 256 KiB image
transfer to frames that previously skipped it; gameplay performance needs
checking alongside visual correctness. No extra VRAM is allocated.

## Verification

`tools/font_refresh.py` executes the actual instructions around both gates,
stubbing only external state queries and upload calls. It tests 16 combinations
of play mode, dialogue state, status flag and resource presence. In the control,
both quiet-frame paths skip the font. In the fix, each valid-resource frame
uploads once; missing resources remain guarded. `first_transfer` also executes
the real 1P descriptor setup and 2P direct-upload setup; both produce PSMCT32,
512x128, buffer width 8 at base 0x2600.

`verify_shared_fonts.py` includes these checks plus startup, glyph, warning,
palette, resource-scope and retained-movie checks. Evidence is in
`work/ui/hud-refresh-0.1.31/frame-trace.json` and the final font verification.
These are instruction/data checks with supplied state, not emulated gameplay
or a captured GS frame. The screenshot's complete render sequence has not
been replayed; fresh-boot warning/name/dialogue checks remain required.

This is a local test build. No release was requested. Mission 23 remains an
unrelated unresolved investigation.

## Local output

`work/output/ACE-EN-0.1.31.iso`, 3,357,147,136 bytes, SHA-256:
`65a238825b9e7b1cfe8cb51dffd61261bc27f01b71ee588746e29b63ac03f43d`.

The build read back its changed resources and all 25 translated movies, and
validated ISO/UDF extents. No release assets have been created or uploaded.

Final font verification passed: four in-game bundle copies, 24 font copies,
both startup uploads, both frame descriptors and all 16 frame scenarios.
Direct comparison with 0.1.30 confirms exactly the two branch words and three
title-stamp texture copies changed. All font bytes, other game resources and
25 movie hashes (including lyrics) are identical. Reports:
`work/ui/hud-speaker-0.1.31/verification.json` and
`work/ui/hud-refresh-0.1.31/scope-verification.json`.
