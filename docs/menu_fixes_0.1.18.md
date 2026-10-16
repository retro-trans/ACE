# Difficulty and controller fixes (0.1.18)

Reported from in-game screenshots on 2026-10-16. Input screenshots are kept locally in
`work/ui/menu-fixes-0.1.18/`.

## Difficulty labels

The difficulty choices are baked into `t0300.tm2` (normal) and `t0301.tm2` (selection/glow).
The previous English drawing boxes began at y=6, 46 and 86, placing the visible lettering above the button
centres. The three English drawing bands move down by five texture pixels to y=11, 51 and 91 in both
textures. Their wording, size, horizontal position and original-source erase boxes stay the same.

## Controller labels

Manual and Semi-Auto use `t0302.tm2` and `t0303.tm2`. The picture is wider than the 512-pixel atlas.
The right edge is stored rotated in the lower atlas. Earlier specs incorrectly treated the complete rotated
labels as a second overlaid panel and erased the horizontal labels. The game actually samples only the
narrow continuation, leaving the last few letters visible.

`b032.mnb`, mesh child 0, has continuation UVs at file offsets `0x4e0` (Manual) and `0x5e0` (Semi-Auto).
Their normalized coordinates, multiplied by 512, are approximately x=196.234..504.888,
y=346.230..404.552. Rounded pixel bounds are `[196,346,505,405]`; rotating clockwise produces a 59x309
continuation beside the 512x309 main rectangle. The rest of the rotated atlas picture is not sampled there.

The texture renderer now supports panel pieces: assemble the main rectangle and continuation, draw all seven
complete right-side labels in their button areas, then return the painted pieces to the original atlas slots.
Texture dimensions, palette, mesh vertices and UVs are unchanged. Both control modes are fixed.
`TextureText` prefers each local working spec over its duplicate `.en.json` export, while still accepting
exports on a fresh checkout.

## Reproduce and check

`tools/controller_panel_spec.py` previews the four spec changes; add `--write` to apply them. It can be rerun
without shifting the labels again. `tools/strip_jp.py` produces the English-only Git exports.

Build with `python tools/build.py 0.1.18 --write --movies MOVIE001,MOVIE002,MOVIE003` after a dry run.
Run `python tools/verify_menu_fixes.py work/output/ACE-EN-0.1.18.iso`, then add `--write` to save proof images
and its report. This compares all DATA.BIN resources with 0.1.17, permits only the four texture replacements
and their packed copies, checks each against its intended encoding, and confirms the executable and controller
mesh UVs are unchanged. Run the standard Japanese-table inventory after the build.

Proofs reconstruct the encoded artwork, not emulator screenshots. In-game confirmation of the button states
and both controller pages remains necessary. This is a local test build; no new release was requested.

## Build results

- ISO: `work/output/ACE-EN-0.1.18.iso`, 3,357,147,136 bytes.
- SHA-256: `28712a4f103890cbb4a04f0c4743fef7e71cad3c98a5e0d1a8de21ad71b3151d`.
- Full dry run and write succeeded, including ISO/UDF layout and on-disc payload hash checks.
- The comparison found only four standalone textures and their copies inside `MenuIntro.csc` and
  `MenuTitleIntro.csc` changed. All three copies of each texture match the intended encoded bytes.
- Every other DATA.BIN resource and the executable are identical to 0.1.17; movie hashes match its report.
- The final Japanese inventory found 0 text tables and 0 rows containing Japanese.
- All four encoded texture proofs were visually reviewed; controller words are complete and difficulty
  labels are vertically centred. Report and proofs: `work/ui/menu-fixes-0.1.18/`.
