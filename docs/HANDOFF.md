# Handoff: Another Century's Episode English fan translation

Project root `E:\Projects\ACE`. Read `AGENTS.md` first: it holds the folder layout and the rules (versioning,
changelog, akurasu as the term source, no Japanese script in git, **no GitHub release without an explicit
request**, releases must work with Retro Trans Tools). The user explicitly requested repository creation and
release 0.1.17 on 2026-10-15, using `binhlt0402` in `retro-trans`. Repository: https://github.com/retro-trans/ACE.
Packaging and publication instructions are in `docs/RELEASING.md`.

## HUD frame refresh: local 0.1.31 (2026-10-26)

pow confirmed the warning banners remain scrambled after a fresh boot of
0.1.30. Startup upload correction alone was insufficient: the shared 0x2600
allocation is transient, but the HUD preparation paths reload the dialogue
atlas only when dialogue/status conditions are true. `build.py` now NOPs the
skip branches at EE 0x1e1ac8 (1P) and 0x1e1b58 (2P), retaining the existing
prepared/direct transfers and null-resource guards. No font data changes.
`tools/font_refresh.py` traces the real branch instructions for 16 scenarios;
0.1.30 quiet frames miss both reloads, and the patched paths refresh every
frame with a valid resource. Both upload descriptors are checked. See
`docs/hud_refresh_0.1.31.md`, `work/ui/hud-refresh-0.1.31/frame-trace.json`.
In-game confirmation/performance remain unverified. No desktop control or
release authorized. Keep all translated movies and lyrics.
Local ISO: `work/output/ACE-EN-0.1.31.iso` (3,357,147,136 bytes), SHA-256
`65a238825b9e7b1cfe8cb51dffd61261bc27f01b71ee588746e29b63ac03f43d`.
Final font/frame and direct 0.1.30 scope comparisons passed: only two branch
words and three title-stamp copies differ. Font bytes, other game resources,
all 25 movies and lyrics are identical. No runtime confirmation yet.

## HUD upload correction: local 0.1.30 (2026-10-26)

pow confirmed the scrambled lock-on name occurs in 0.1.29 after a fresh boot.
The HUD startup calls at EE 0x1e165c and 0x1e17ec still called the linear
uploader 0x17c530, which ignores the mode word and misinterprets the new
swizzled texture data. `build.py` now changes both JALs to 0x17d1d0 when shared
fonts are enabled. No atlas/metrics/palette changes are needed. The instruction
trace in `tools/font_upload.py` rejects the 0.1.29 path and checks the correct
512x128 PSMCT32 transfer for both corrected calls. `verify_shared_fonts.py`
includes these checks. See `docs/hud_upload_0.1.30.md` and evidence under
`work/ui/hud-upload-0.1.30/`. Local testing only: no release requested, no
desktop control. User gameplay confirmation is still required.
Completed ISO: `work/output/ACE-EN-0.1.30.iso` (3,357,147,136 bytes), SHA-256
`f608d4e320e5d95506ed3f950640d99a6d371f69c0c0285d89adfb2a27d1efa0`.
Font/upload checks and Japanese-table scan (0 tables/rows) passed. Direct comparison
with 0.1.29 confirms only the two executable calls and three title-stamp copies
changed; all fonts, mission data, 25 movie hashes and both lyrics are unchanged.

## Shared 4x fonts: released 0.1.29 (2026-10-22)

Upgrade repair (2026-10-22): the initial release only included an original-disc
patch, so Retro Trans Latest stayed on 0.1.26 and explicit 0.1.29 had no path.
The user's report authorized repairing this existing release. Added
`ACE-English-0.1.26-to-0.1.29.xdelta` (92,975,382 bytes), fully round-tripped from
the published 0.1.26 ISO to the identical published 0.1.29 output. Both patch
entries preserve the published game identities; the original full-patch asset
ID, URL, bytes and checksum remain unchanged. The package now has five assets.
Augmented local package: `work/output/release-0.1.29-upgrade-from-0.1.26/`.
Initial metadata/checks: `docs/releases/0.1.29/initial-publication/`; repair
evidence: `docs/releases/0.1.29/upgrade-from-0.1.26/`. Use
`tools/add_release_upgrade.py` and `verify_release_routes.py --upgrade-from`
for future release upgrades. Canonical metadata under `docs/releases/0.1.29/`
now describes both routes.
Catalog refresh run `39703037475` succeeded. Public catalog checks confirm
Latest, explicit 0.1.29 and Next version only all upgrade 0.1.26 directly to
0.1.29; the original-disc routes, current-image no-op and unknown-image rejection
also pass. The user should click Refresh catalog and reselect the 0.1.26 ISO.

Published: https://github.com/retro-trans/ACE/releases/tag/v0.1.29.
Source commit: `009da80a6b7c18f71ec0da922cf9041ff9c9570d`; release metadata commit:
`e4d6bf2`. The initial four-asset package passed a full round trip and uploaded size/SHA-256
checks. Canonical package and validation evidence: `docs/releases/0.1.29/`.
Initial Retro Trans catalog refresh run `39665115701` succeeded. The public catalog routes
both Latest and explicit 0.1.29 from the original Japanese ISO to this release;
already-current images are a no-op and unknown images are rejected. Reports:
`catalog-workflow.json`, `public-routes.json`, and `uploaded-assets.json` in that folder.

The user reported blocks in multiple speaker names and lock-on labels, then requested
removing Japanese glyphs to save space. `english_fonts.py` reclaims unused Japanese glyphs
and compacts the maps/records. The two in-game fonts now use separate regions of the same
1024x512 PSMT4 atlas at the existing dialogue GS base 0x2600. Their palettes remain separate.
`build.py` changes only the HUD base word at EE 0x2a64d8, from 0xc00 to 0x2600. The larger
PSMT4HH HUD allocation from 0.1.23 is superseded. Main menu atlases are reduced to 1024x512.
Use `verify_shared_fonts.py`, not the historical standalone `verify_hud_hd.py`, for current
builds. See `docs/shared_fonts_0.1.29.md`. Keep all 25 translated movies and lyrics.
The user explicitly requested release 0.1.29 on 2026-10-22. Packaging/publication is
authorized; desktop control remains unauthorized. See `docs/RELEASING.md`.
Completed ISO: `work/output/ACE-EN-0.1.29.iso`, 3,357,147,136 bytes, SHA-256
`02ad1831f30daf61348b24cdeb176e1be3bee019cfad7fefcac7a846844f7f6f`.
The final font/scope comparison passed; all four in-game bundles are correct, other
game data and all 25 movies/lyrics match 0.1.28 except the title version and intended
font changes. Japanese-table scan: 0 tables/rows. Evidence and reconstructed previews:
`work/ui/hud-speaker-0.1.29/`. Fresh boot plus a normal memory-card save is required for
the user's runtime check; an old save state can restore the broken font/code.

## Story subtitle fade correction: local 0.1.28 (2026-10-22)

The user reported Japanese flashing before English in story movies. The bright-stroke scan
missed faint fades: typically 11 frames per subtitle edge and 17 per title edge. All 171 cards
in the 22 story movies now use measured low-contrast ranges with a two-frame guard, clipped
in short gaps to prevent overlap. `tools/subtitle_timing.py --write` updates both the specs
and source cards; `subtitle_spec.py` preserves this metadata during regeneration.
`StaticCard` measures opacity on `ink_rows` for these cards, avoiding live-picture interference.
`tools/verify_subtitle_fades.py` checks decoded edges for remaining source lettering.
Evidence is in `work/ui/movies/subtitle-timing-0.1.28/`. The reported clip is `M1_MOVIE011`,
card 5: bright scan [720,871), visible source [709,882). See `docs/movies.md`.
All 22 rebuilt movies passed the encoded check: 171 cards, 5,849 unique edge frames,
zero failures. The encoded comparison also confirms clean blank frames 708/882 in
the reported clip. This is decoded-file verification, not emulator playback.
Use the standard full build with all 25 translated movies and lyrics. This build retains
English mission dialogue; do not apply the 0.1.27 diagnostic. No release was requested.
Completed ISO: `work/output/ACE-EN-0.1.28.iso`, 3,357,147,136 bytes, SHA-256
`c338b3476f280ac3658a592d389bedefb2733500b2960ca05e81091063be46c2`.
Final resource comparison against 0.1.26 passed: only three title-version texture copies
change outside the story movies; all English mission data, fonts, prior UI fixes and
opening/ending movies match. Japanese-table inventory: 0 tables, 0 rows.
Movie-scope verification passed for all 25 translated movies, including both lyric overlays:
on-disc hashes match and original packet positions/audio/nonvideo bytes are unchanged.
Final reports are `work/output/ACE-EN-0.1.28.movies.verify.json` and `.restore.verify.json`.

## Mission 23 investigation (2026-10-22)

The latest-public 0.1.26 player reported all enemies defeated but no mission end.
Save: `incoming/ace_mission23.ps2`; campaign mission 23 maps to internal **025**, not 023.
No cause or fix is confirmed. Released text preserves control tokens and passes existing
layout checks; mission map/enemy/AI logic matches the Japanese original. The user asked
to continue without desktop control. Do not resume UI automation without new permission.
Local **0.1.27 dialogue diagnostic** restores only mission 025 dialogue to Japanese,
retaining English objectives, other translations, movies and lyrics. Replay from a normal
save and fresh boot to isolate dialogue effects. See `docs/mission23_investigation.md`.
This is not a public release; no release request was made for this build.

## Release 0.1.26 (2026-10-21)

The user explicitly requested a release of the current build. Published **0.1.26**, retaining
lyrics and all 22 restored story movies. The discussion of "upstairs" only explained the idiom; that dialogue
was not edited and is unchanged in this build. Release notes: `docs/releases/RELEASE_NOTES_0.1.26.md`.
Release: https://github.com/retro-trans/ACE/releases/tag/v0.1.26. Packaging passed the full encode/decode
round trip and candidate Retro Trans routing checks. All four uploaded sizes and SHA-256 digests match.
Retro Trans catalog refresh run: `39595847574` succeeded. Public Latest and explicit-version routing select
0.1.26; current-image no-op and unknown-image rejection passed. Publication evidence is under
`docs/releases/0.1.26/`. Preserve the documented distinction between automated checks and outstanding
gameplay verification, especially the expanded 4x HUD font allocation.

## Launch information panels (2026-10-21)

Local build **0.1.26** fixes repeated/stretched lettering after `Resources` and `Repair Eff.` on Launch Setting.
`t0802.tm2` is a 256x128 atlas. Both `b081.mnb` (launch) and `b083.mnb` (unit setup) reuse narrow horizontal
strips, so English growth past the fixed section caused the screenshot artifacts. `tools/launch_panel_spec.py`
keeps Resources within x=23..86 and Repair Eff. within x=22..85, while separately erasing the original text.
Wording and font height are unchanged. `tools/verify_launch_panel.py` checks both meshes, the clean repeated
strips, unchanged adjacent labels/percent sign and optional ISO differences from 0.1.25. Reconstructed proofs
are under `work/ui/launch-panel-0.1.26/`; the before image reproduces both reported artifacts exactly.
Completed ISO: `work/output/ACE-EN-0.1.26.iso`, 3,357,147,136 bytes, SHA-256
`95b7fafe2b4c5ddbfbd276f1322cb4cc08479891af0b714db3520b481472244c`.
Final comparison passed: three launch texture copies (standalone, MenuCampaign, MenuFree) and three title
version copies match; all other resources and disc files, including movies/audio and the carrier fix, match
0.1.25. Japanese-table inventory: 0 tables, 0 rows. Evidence: `work/ui/launch-panel-0.1.26/verification.json`.
In-game confirmation remains necessary. Release was subsequently requested; see the release section above.
See `docs/launch_panel_0.1.26.md`.

## Carrier information panel (2026-10-21)

Local build **0.1.25** fixes split/overlapping labels in the Rendezvous Point carrier-info panel. Texture
`t0403.tm2` is stretched by object 32 of `b043.mnb`: atlas x=94.1005..94.2618 fills most of the value column.
The old English specs grew into this strip and the right border. `tools/carrier_panel_spec.py` removes that
growth, keeps the heading within x=21..90, abbreviates the name labels to `Carrier`/`Squad`, and bounds body
labels to x<=86. `texture_text.render_label` now accepts `erase_box` so the entire original heading is erased
even when its replacement drawing box is narrower. Other label rendering is unchanged.
`tools/verify_carrier_panel.py` reconstructs the encoded panel using the mesh UVs and can compare a final ISO
with 0.1.24. Before/after proofs are in `work/ui/carrier-panel-0.1.25/`; they reproduce the reported artifacts
and show the corrected label area. These are reconstructions, not emulator screenshots.
Completed ISO: `work/output/ACE-EN-0.1.25.iso`, 3,357,147,136 bytes, SHA-256
`4cf79a34ff43d8d1e0f166f69330352c3128d3f2d5a69f52ba012688f5137b7c`.
Final comparison passed: both carrier-texture copies and three title-version copies match the intended
encoding; all other resources and disc files (including the mesh, executable and all movies) match 0.1.24.
Japanese-table inventory: 0 tables, 0 rows. Report: `work/ui/carrier-panel-0.1.25/verification.json`.
In-game confirmation remains necessary. No release was requested. See `docs/carrier_panel_0.1.25.md`.

## Story movie translations restored (2026-10-21)

The user explicitly requested restoring the translated story movies. **All 22 `/MOVIE1` translations are
active again for local build 0.1.24**, superseding the old exclusion recorded below for 0.1.16-0.1.23.
Their specs now live directly in `work/translation/en/movies/`; do not move them back to `disabled/`.
Build with `python tools/build.py 0.1.24 --write` (all 25 active movie specs), retaining both lyric overlays,
the 4x HUD font and automatic title version. Do not use the old three-movie `--movies` restriction.
`verify_movie_scope.py` now requires all 22 translated story movies by default and checks their unchanged
audio/nonvideo data. Use `--original-story` only to verify historical builds 0.1.16-0.1.23.
Completed: `work/output/ACE-EN-0.1.24.iso`, 3,357,147,136 bytes, SHA-256
`afde085f60e6d04d3f83f0fa8dbbd4216d5155e9297541ca94eeca8b35f2cc89`.
All 25 on-disc movie hashes, packet positions and unchanged audio/nonvideo checks passed. All 22 story
movies decode to their expected frame counts. Encoded title/dialogue frames from the reported Gavlet clip
were visually checked and saved under `work/ui/story-movies-0.1.24/`. The resource comparison against 0.1.23
passed: only three copies of the title-version texture differ outside the movies; the 4x HUD font, other
game data and other disc files are unchanged. Japanese-table inventory: 0 tables, 0 rows. Both songs' 52
lyric rows pass their layout checks. Reports/logs are beside the ISO (`.movies.verify.json`,
`.restore.verify.json`, `.story-check.log`, `.inventory.log`). In-game playback and the 4x HUD allocation
still require gameplay confirmation. No GitHub release was requested for 0.1.24.

## Speaker-name font (2026-10-21)

Local build **0.1.23** upgrades HUD font 50071/50051 (speaker names and lock-on labels) from 1x to 4x.
`tools/hud_font_hd.py` expands the linear PSMT4HH atlas from 256x128 to 512x512. Text metrics, palette and
stock warning glyphs are preserved. No executable modifications. **Runtime validation of the larger GPU
allocation is required before treating this as release-ready.** See `docs/hud_font_0.1.23.md` and use
`tools/verify_hud_hd.py` for the new build; the historical 0.1.19 warning verifier assumes unchanged 1x ASCII.
Lyrics remain included. No GitHub release was requested.
Output: `work/output/ACE-EN-0.1.23.iso` (3,357,147,136 bytes), SHA-256
`1410084f4bd46f00eb8dcd30d99f56555730d3e0758179c2c50b59672bbe2446`.
Final ISO comparison passed for all four font copies; other game data, executable and movies match 0.1.22
apart from the automatic title label. Japanese inventory: 0 tables, 0 rows. PCSX2 testing was not completed:
another game started in the shared emulator. Temporary keyboard mappings were restored in the saved Pad1
configuration, but the running session may retain them until settings reload/restart. Do not interrupt it.

## Title version and group credit (2026-10-17)

Local build **0.1.22** adds `v0.1.22` and `github.com / retro-trans` at the bottom right of the title screen,
following the user's SRW Z screenshot. The version is generated automatically from the build argument.
`tools/title_stamp.py` stamps the translated `t3105.tm2`; two bounds in `l014.mnl` extend the copyright sprite
to the right without moving or scaling the existing credits. It preserves all existing artwork and uses the
original palette. Coordinates and reproduction details: `docs/title_stamp_0.1.22.md`.
Reconstructed previews and checks are under `work/ui/title-stamp-0.1.22/`; they are not emulator screenshots.
The build retains 0.1.20's mission 3 fix and all three edited movies, including both lyric overlays.
Output: `work/output/ACE-EN-0.1.22.iso`, 3,357,147,136 bytes, SHA-256
`2030fc1dddce477c80aa1b7692ad80164eefe4c3408e500dd6dddbc3807deb7d`.
Final ISO comparison passed: three copies each of the title texture/layout, unchanged unrelated resources,
executable and movie identities. Japanese-table inventory: 0 tables, 0 rows.
Fresh-boot title-screen confirmation remains for user testing. No release was requested for this build.

## Public release

The user explicitly requested a new release on 2026-10-16 and confirmed that lyrics must be included.
Published release: https://github.com/retro-trans/ACE/releases/tag/v0.1.20.
The image is **0.1.20**, SHA-256
`45148f8c96a06d8cc5129de216dcf0f36830cb3f82f4f4f1c82652af79168082`.
It includes the play-confirmed mission 3 progression fix, the 0.1.18 menu fixes, the restored HUD warnings,
and both opening/ending lyric overlays. The lyric-free 0.1.21 image is a local variant and is not selected
for publication. Release notes: `docs/releases/RELEASE_NOTES_0.1.20.md`.
The 320,364,671-byte xdelta passed a full decode-and-hash round trip. Its SHA-256 is
`0548bd3bc952e36b238c427341ddd54bf2c992238208f1a5552f18a63f69cf7c`.
All four uploaded assets matched local sizes and digests. Records are under `docs/releases/0.1.20/`.
Source commit: `680bde7c1a75f2d8c5d813e6d09b2a0101a1380a`; tag target: `24f79fdf4c651d6e498ba5b9fb58d27a7ea2bcf3`.
Retro Trans catalog refresh `38926031385` succeeded. The downloaded public catalog routes the original disc
to 0.1.20 for Latest or explicit 0.1.20, treats the current image as a no-op, and rejects unknown images.
Next version only still selects 0.1.17, the earliest public release. Use Latest or explicit 0.1.20.

### Previous public release

Build **0.1.17** is published at https://github.com/retro-trans/ACE/releases/tag/v0.1.17.
The release contains `ACE-English-0.1.17.xdelta` (320,312,789 bytes), the Retro Trans manifest,
validation report and checksums. Its patch SHA-256 is
`7f021fa068408aafe089cf8244662384b0b1583caaade3683da2ede4278dd10d`.
The upstream release builder decoded the patch and verified the complete image against the build checksum;
all uploaded asset sizes and GitHub SHA-256 digests matched. Evidence is in `docs/releases/0.1.17/`.
Retro Trans catalog refresh run `38605374725` succeeded. The downloaded public catalog passed original-disc
routes for Latest, Next version only and 0.1.17, current-image no-op and unknown-image rejection.
The source commit is `219b6e5d65ea5515356bef428d25989b55c152dc`; the release tag also includes packaging records.
Future changed builds need a new version and a new explicit publication request.

## HUD warning restoration (2026-10-16)

Earlier local image: `work/output/ACE-EN-0.1.19.iso` (3,357,147,136 bytes; SHA-256
`0cae3a989e87bb8b2fabb61bc058d185b2bfcb9a964fead4e8b0b0a6e28a232f`).

The user reported question marks where the original game displays `AREA OVER`. Build **0.1.19** preserves
the stock full-width English glyphs for `AREA OVER`, `CAUTION`, `ON AIR`, `MISSILE`, and `ERROR` in the HUD
font. These strings are in `Fe1p.bnd` and `Fe2p.bnd`, nested child `50140/5`; they had escaped the Japanese
inventory because they were already English. The font rebuild had remapped their characters to `?`.
`tools/ui_layout.py` now retains those original glyphs, and `tools/verify_hud_warning.py` checks their exact
pixels and metrics plus unchanged translated ASCII glyphs. See `docs/hud_warning_0.1.19.md`.
The built ISO passed the font comparison: only HUD fonts changed from 0.1.18; other DATA.BIN resources and
the executable are identical. Movie hashes match; ISO/UDF and payload checks passed. The final Japanese
inventory found 0 tables and 0 rows. Local font proofs and verification are in `work/ui/hud-warning-0.1.19/`.
In-game confirmation of the warning remains for user testing. No release was requested for this build.

## Local menu fixes (2026-10-16)

Build **0.1.18** fixes the user-reported difficulty alignment and clipped controller labels.
Previous local image: `work/output/ACE-EN-0.1.18.iso` (3,357,147,136 bytes; SHA-256
`28712a4f103890cbb4a04f0c4743fef7e71cad3c98a5e0d1a8de21ad71b3151d`).
Rookie/Pilot/Ace move down five texture pixels in both normal and highlighted states.
Manual and Semi-Auto right-side labels are now drawn across the main texture and its rotated continuation,
using the actual `b032.mnb` UV bounds. See `docs/menu_fixes_0.1.18.md` for coordinates and reproduction.
Encoded artwork is reconstructed under `work/ui/menu-fixes-0.1.18/`; these are not emulator screenshots.
The saved `verification.json` confirms all three copies of each texture, unchanged other DATA.BIN resources
and executable, and the controller mesh UV bounds. The build's ISO/UDF and payload hash checks passed;
movie hashes match 0.1.17. All four encoded-artwork previews were visually reviewed.
The 0.1.18 Japanese inventory found 0 text tables and 0 rows containing Japanese.
Both controller pages and all three difficulty selections still need in-game confirmation from a fresh boot.
This build was not published individually; its menu fixes are included in public release 0.1.20.

## Previous image and validation (2026-10-15)

Previous image: `work/output/ACE-EN-0.1.17.iso` (SHA-256
`198bfe6cbd177347927aa412e716197f0d148e06ad768ee94537ac39b8e5871c`). The ending now uses a larger lyric
overlay across the bottom of the credits and an English replacement epilogue scroll. All 22 story movies are
original. All text outside the movies is translated and checked.
The user previously confirmed these game screens and sequences (before the recent movie changes):
- mission 1, including the tutorial and the aerial combat;
- mission 2's briefing;
- the title screen;
- the save screen.

`docs/CHANGELOG.md` includes the 0.1.20 release and the unselected 0.1.21 local movie variant.

Static checks on 0.1.17:
- `tools/japanese_inventory.py` finds 0 text tables with Japanese.
- `verify_no_japanese.py --textures-only`: 35 original Japanese-lettered textures checked, 0 left.
- `dialogue_layout.py check` and `briefing_layout.py check` report 0 problems.
- `verify_karaoke.py`: all 52 sung rows pass layout, translation coverage and highlight checks.
- `verify_movie_scope.py`: exactly 3 translated movies; all 22 story movies match the source byte for byte;
  every audio packet and other nonvideo byte is unchanged.
- Built PSS and MP4 frame counts match the originals: MOVIE003 5,410; MOVIE002 14,342.
- `verify_epilogue.py`: all 1,920 replaced frames passed, with no surviving Japanese strokes detected.

Japanese that remains on the disc and is never shown to players:
- `.def` parameter field names;
- `CharGame.prm` debug units;
- event and motion script labels;
- a debug test scene.

## Hard limits learned in play (do not loosen)

Two buffers turned out to be sized for the Japanese: a longer line froze or crashed the game (PCSX2 assertion
"FQC = 0 on VIF FIFO READ"). Every text is now held to the Japanese maximum, or to a length proven in play. All of
these are enforced by the layout checks and the build:

| Text | Limit |
| --- | --- |
| Operator window (`<op()>` ... `<ed()>`) | 1 line, 54 visible bytes |
| Operator window with speaker color (`<cs(n)>`) | 1 line, 46 visible bytes |
| Main radio window | 2 lines, 93 bytes |
| HUD objective labels (rows 1-9 of each mission) | 28 bytes |
| Briefing text | 89 bytes |
| Briefing objectives | 39 bytes |
| Mission names | 27 bytes |
| Menus, HUD, encyclopedia | the Japanese maximum of each group (`work/translation/en/ui/*.json` limits) |

See `docs/dialogue.md` and the header of `tools/briefing_layout.py`. To find a crash, bisect with diagnostic
builds: `build.py VERSION --write --stock-missions 001 | --stock-labels 001 | --stock-dialogue 001 |
--rows "001:!67-69" | --stock-hud | --no-cleanup | --no-blank`.

## Build

- `python tools/build.py 0.1.N --write`: 32-bit Python 3.8 at `C:\Python`, about 10 minutes, writes about 3.3 GB.
- `--movies A,B` limits which movie specs are included.
- Finish changed movie builds before starting the ISO build; the movie readiness check runs after game-data
  preparation, and a stale movie report stops the build before the ISO is written.
- Each build writes `work/output/ACE-EN-0.1.N.json` next to the ISO.
- After a build, run `python tools/japanese_inventory.py <iso>`, then update the changelog.
- Before any commit, run `python tools/strip_jp.py`. It writes the `*.en.json` copies, the only translation files
  that may be committed.

## Movies

Tools:
- `tools/movie_text.py`: segments, preview, build and splice. Re-encoded GOPs must fit the original GOP's bytes;
  the PSS keeps its size.
- `tools/movie_export.py`: MP4 export to `work/output/mp4/` (originals) or `work/output/mp4/built/` (`--built`).
- `tools/caption_spec.py`: subtitles drawn over the picture.
- `tools/karaoke_spec.py`: karaoke segments.
- `tools/whisper_tool.py`: speech transcript and song timing. Run it with the 64-bit venv
  `.venv-whisper/Scripts/python.exe` (CUDA, faster-whisper large-v3).

Background: `docs/movies.md`.

What the user wants:
- **MOVIE001 (opening news broadcast):** English subtitles for the speech plus the translated scrolling
  statement. **Done.**
  - Captions: `work/translation/en/movies/captions/MOVIE001.json`.
  - Built: `work/output/mp4/built/MOVIE001.mp4`.
  - Possible follow-up: a few explosion GOPs during the captions were re-encoded at qscale 7-12 to fit, so check
    for blocking. Better ffmpeg mpeg2 settings (trellis, rd macroblock decision) could recover quality at the same
    size.
- **MOVIE002 (ending):**
  - The epilogue's Japanese is replaced directly by an English scroll. The separate sentence
    subtitles are removed. Use `tools/epilogue_spec.py`; `captions/MOVIE002.json` is its reference translation.
  - The staff roll, producer cards and publisher card are replaced with English. **Done.**
  - The ending song has 21 rows of romaji karaoke and English translation. On 2026-10-15 the user selected a
    larger overlay across the bottom of the credits: 18 px romaji, 15 px English, translucent dark backing.
- **MOVIE003 (opening song before the title):** 31 sung rows of Garnet Moon karaoke with the user's English
  translation. Seven supplied rows are omitted in this shorter movie arrangement.
- **MOVIE005:** ignore it.
- **The 22 story cutscenes (`/MOVIE1`):** restore their English title cards and subtitles, explicitly requested
  on 2026-10-21. Specs are active in `work/translation/en/movies/`. The exclusion in 0.1.16-0.1.23 is historical;
  0.1.24 restores the translated versions. `verify_movie_scope.py` checks all 25 replacements and their audio.

### Karaoke: supplied lyrics and verification

The user supplied both songs and requested their inclusion. The agent may process those supplied lyrics for
this task. Keep their text in the git-ignored `work/translation/en/movies/lyrics/` folder; keep row indices and
timings in movie specs. The original supplied two-block files are preserved as `MOVIE00N.provided.txt`; working
`MOVIE00N.txt` files now use meaning-matched `romaji || English` rows. English wording has been preserved.

`tools/prepare_song_pairs.py` contains the reviewed row-number mapping, with no lyrics. The shared reader in
`tools/lyrics.py` rejects ambiguous unpaired two-block files instead of guessing translations by line count.
`whisper_tool.py align` now reads romaji only and accepts `--from`, `--to` and `--rows` to align difficult
passages. It keeps recognition text in memory and saves only numeric timing evidence and a lyrics-file hash.

`tools/finalize_song_timing.py` combines the successful local alignment windows. Final evidence is copied into
`work/ui/movies/karaoke/MOVIE00N.timing.json`. The opening vocals start around **42.58 s**, not the earlier
60-second estimate, and finish around 171.34 s. Ending sung phrases run about 126.64..441.03 s. Timings are
automatic; phrase coverage and numerical order have been reviewed, but final listening review remains.

`karaoke_spec.py` creates romaji and separate English caption segments. Repeated translations stay on screen
across adjacent phrases; wrapped romaji highlights across each line. Movie build hashes include external lyric
file contents, so changing a lyric requires rebuilding the movie.

```text
python tools/karaoke_spec.py MOVIE003
python tools/epilogue_spec.py
python tools/karaoke_spec.py MOVIE002 --layout overlay
python tools/verify_karaoke.py
python tools/movie_text.py build MOVIE003
python tools/movie_text.py build MOVIE002
python tools/verify_epilogue.py
python tools/movie_export.py --built MOVIE002 MOVIE003
python tools/build.py 0.1.17 --write --movies MOVIE001,MOVIE002,MOVIE003
python tools/japanese_inventory.py work/output/ACE-EN-0.1.17.iso
python tools/verify_no_japanese.py work/output/ACE-EN-0.1.17.iso --textures-only
python tools/verify_movie_scope.py work/output/ACE-EN-0.1.17.iso
```

`verify_karaoke.py` checks all 52 sung rows for translation coverage, line overlap, frame bounds, full highlight
and layout-specific bounds/backing. Reports and encoded preview frames are in `work/ui/movies/karaoke/`.
`verify_epilogue.py` checks the encoded replacement scroll for surviving Japanese strokes in every frame.
The 0.1.17 check passed all 1,920 frames; a versioned report is beside the ISO (`.epilogue.verify.json`).
`verify_movie_scope.py` verifies every movie on disc, all 22 original story files and unchanged nonvideo bytes
(including audio) in the three rebuilt movies. The movie part of `verify_no_japanese.py` predates additive
captions and karaoke; use its `--textures-only` option for the texture check.

### User playtest still needed

Review `work/output/mp4/built/MOVIE003.mp4` and `MOVIE002.mp4` for sung timing, then check the opening, ending
and transition to the title screen in game. Encoding and static checks do not establish playback on PS2/PCSX2.
The versioned ending preview is `work/output/mp4/0.1.17/ending.mp4`; encoded samples and lyric bounds are in
`work/ui/movies/0.1.17/`.

## Other notes

- **Fonts:**
  - The dialogue font is patched at 2x.
  - f010 (menus) is HD at 4x.
  - f005 and the HUD font are rebuilt to hold only the glyphs they use.
  - Details in `docs/vwf.md`.
- **Textures:** 35 relettered (`work/translation/en/textures/`, `docs/ui_and_textures.md`). The controller screen's
  right-column labels are drawn from rotated strips, so the panel copies are erased (t0302/t0303).
- **Heredocs:** they mangle backslashes and can write NUL bytes into Python files. Write scripts to files with the
  editor instead, and check with `python -c "import ast; ..."`.
- **Subagents:** be conscious of the user's subscription limits (AGENTS.md).
- **Open question:** should AGENTS.md's akurasu link point to the ACE page instead of the SRW MX page? The user has
  not answered yet.
