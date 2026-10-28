# Changelog

## 0.1.38 - 2026-10-28

- Public release requested by pow. Includes all local changes from 0.1.33–0.1.37:
  runtime story subtitles, lossless movie repacking, Slot Info labels, briefing
  conditions and lock-on name capacity. Retains English lyrics and karaoke.
- Package original-disc and direct public 0.1.32 upgrade routes for Retro Trans.

- Fix radio speaker names stopping after 12 characters (`Titans Soldi`). Raise
  the speaker draw/reveal count to the translation budget of 22 characters.
  Keep the existing 50-glyph drawing allocation and font size unchanged.
- Retain full translated names, the 4x font and all 0.1.37 fixes and lyrics.
- Verify all 69 names and execute the speaker wrapper to check the new count
  and unchanged font arguments. The final ISO changes only one executable
  immediate and three title stamps. Fresh-boot gameplay confirmation pending.

## 0.1.37 - 2026-10-28 (local test build; not released)

- Fix target names stopping after 12 glyphs, such as `Jonathan's G`. Raise the
  lock-on widget's drawing limit to 24 glyphs, and increase
  its drawing allocation to match (1,520 to 2,864 bytes per widget).
- Preserve full translated names and the existing 156-unit width limit. All
  104 lock-on labels fit; 15 exceed the old cap, with a maximum of 19 glyphs.
- Retain 0.1.36 briefing fixes, Slot Info labels, movie pacing and all lyrics.
- Verify native allocation arithmetic, all labels and final ISO scope: only
  two capacity constants and version stamps change. Font size remains 12.
  Fresh-boot gameplay verification remains pending; old save states retain
  the original code and allocation.

## 0.1.36 - 2026-10-28 (local test build; not released)

- Fix the incomplete `Escort the` victory condition in Intercept E2 Launch:
  use `Escort friendly warship` on one line. The condition panel does not show
  the second line previously inserted by the layout tool.
- Fix the same wrapping issue in the city-damage defeat condition and speech
  victory condition. Validate victory/defeat labels as single-line fields;
  retain two-line secret objectives and dialogue. All 801 briefing rows pass.
- Retain 0.1.35 Slot Info labels, movie pacing, translations and lyrics.
- Verify all nine briefing-table copies and three version stamps; all other
  resources, executable and movies match 0.1.35. Live gameplay not checked.

## 0.1.35 - 2026-10-28 (local test build; not released)

- Shorten the Slot Info weapon-stat labels to `Power` and `Reload`, under the
  existing Weapon heading, to leave room before the stat bars. Preserve weapon
  categories, bar positions and values in both Campaign and Free Missions.
- Retain 0.1.34 movie pacing, runtime story subtitles, translations and lyrics.
- Verify the encoded texture preview and all three on-disc copies. Only Slot
  Info labels and version stamps differ from 0.1.34; live gameplay not checked.

## 0.1.34 - 2026-10-28 (local test build; not released)

- Fix repeated movie frame-group pauses by moving excessive zero stuffing out
  of MPEG video payloads into standard program-stream padding packets. Repack
  the news, opening and ending without re-encoding pictures or changing audio,
  timestamps, lyrics or file sizes. All decoded frames match their prior versions.
- In an isolated replay of the supplied credits state, the matched frame range
  1500–4500 improved from 29.13 to 29.96 decoded frames/second; consecutive-frame
  gaps over 60 ms fell from 56 to 2. Display synchronization alone did not help.
  This is measured improvement in PCSX2 2.8.2, not a claim of zero stutter on all systems.
- Keep the runtime story captions and original story-video quality from 0.1.33.
  Build with `--movie-overlay --movie-pacing`; retain all translations and karaoke.
  Add a read-only playback tracer and full-frame repacking checks. No release.
- Final movie/game-data checks pass against 0.1.33: only the three MOVIE0
  repacks and version stamps differ. Normal emulator settings remain unchanged.

## Movie exports - 2026-10-27 (no build change)

- Export the opening song and ending credits directly from the 0.1.29 ISO
  into `work/output/mp4/0.1.29/` for offline stutter comparison. Preserve
  translated captions/lyrics, native 30000/1001 frame cadence and soundtrack;
  use high-quality H.264/AAC with 4:3 display metadata. No game files change.

## 0.1.33 - 2026-10-27 (local test build; not released)

- Restore original video bytes in all 22 story movies and render their 171
  English captions/title cards onto decoded pictures during playback. Keep
  the corrected fade coverage and existing font rendering; retain all three
  translated opening/ending movies, English lyrics and romaji karaoke.
- Reserve overlay memory through an ELF load segment and updated heap bounds.
  Caption timing follows queued movie pictures; no gameplay font or new GS
  packet is used. Add CPU execution, pixel-coverage and movie-scope checks.
- Update all three title stamps to 0.1.33. Fresh-boot playback/gameplay testing
  is still required; no credit-stutter fix or mission-completion claim.
  See `docs/movie_overlay_0.1.33.md`.
- The original-disc patch shrinks from 890,566,740 to 319,280,205 bytes
  (64.15%). Retro Trans Tools full decode matches the new ISO SHA-256.
  All 953 CPU frame cases and movie/game-data scope checks pass.

## Patch-size investigation - 2026-10-27 (no build change)

- Produce a local compact patch for the identical public 0.1.32 ISO, saving
  3,536,293 bytes (0.397%). Full Retro Trans Tools decode and SHA-256 verification
  pass. Published assets remain unchanged.
- Assess runtime movie subtitles: inventory 148 bottom-bar captions and 23
  title cards, and locate movie loading/drawing routines for further work.
  No runtime overlay is implemented. Record findings in
  `docs/movie_overlay_feasibility.md`; all translations and lyrics remain intact.

## Investigation - 2026-10-27 (no build change)

- Inspect the supplied ending save state without desktop control and add a
  full-movie cadence/packet-clock audit. All 14,342 ending frames and unchanged
  audio pass offline checks. Two picture starts near 2:44 show a scheduling
  risk; the reported runtime microstutter remains unconfirmed. Save findings
  and a short reference clip. No stutter fix or release is claimed.

## 0.1.32 - 2026-10-27 (released; built 2026-10-26)

- Published with explicit authorization as `v0.1.32`. Both the original-disc
  patch and direct public-0.1.29 upgrade passed full reconstruction checks.
  All five uploaded asset sizes and SHA-256 digests match the verified package.
  Opening/ending lyrics and all translated movies are included. This release
  does not claim verified mission completion or a credit-stutter fix.
- Retro Trans catalog refresh `40456417631` succeeded. Public discovery checks
  pass for original-disc and direct 0.1.29 upgrades, plus the existing two-step
  route from 0.1.26. Earlier release identities remain unchanged.
- Documentation correction: pow confirmed the earlier Jeril retreat screenshot
  was mission 23, matching internal 025. Keep its unverified completion issue
  separate from the newer internal-044 hang-state evidence. No build change.
- Fixes an undersized operator-dialogue drawing buffer exposed by the saved
  mission 39 hang. The game reserved space for 50 glyphs but drew a 53-character
  English message, overwriting 336 bytes of neighbouring heap data. The saved
  graphics packet then requested megabytes of unrelated data and stalled.
- Expands that one allocation to 128 glyphs. Existing translation/layout limits
  remain unchanged. Retains the 4x fonts, movie subtitles, karaoke and lyrics.
- Adds a saved-memory regression check and a translation-budget audit. These
  verify the overflow and increased capacity; mission completion still needs
  a fresh-boot gameplay test. Do not resume the already-corrupted save state.
- This also removes the same allocation hazard from earlier missions; it does
  not establish that the previously reported post-retreat stalls are resolved.
  See `docs/dialogue_buffer_0.1.32.md`. Release explicitly requested on 2026-10-27.
- Finished ISO passes the allocation audit and full comparison to 0.1.31:
  only EE 0x2018dc and three title stamps change; all other resources/files
  match, including movies and lyrics. Local ISO SHA-256:
  `72d807e7b9e8f02f54b2ff3f491ed0fdb60c4cbf15dabdb81a0195217b248f73`.

## 0.1.31 - 2026-10-26 (local test build, not released)

- Addresses scrambled warning banners reported after a fresh boot of 0.1.30.
  The shared atlas was refreshed only while dialogue was active, although its
  GS allocation is reused. Both 1P and 2P now reload it for every HUD frame.
- Changes two conditional branches; retains the existing upload routines,
  synchronization and null-resource guards. All font pixels, glyph maps,
  English metrics, palettes, translations, movies and lyrics are retained.
- Adds actual-instruction frame-gate checks for 16 combinations of play mode,
  dialogue state, status flag and resource presence. Quiet frames reproduce
  the missing refresh before the fix. Both transfer descriptors are traced.
- Offline checks do not replace a fresh-boot gameplay/performance check.
  No release requested. See `docs/hud_refresh_0.1.31.md`.
- Local ISO: `work/output/ACE-EN-0.1.31.iso`, SHA-256
  `65a238825b9e7b1cfe8cb51dffd61261bc27f01b71ee588746e29b63ac03f43d`.
- Final font/frame checks and direct comparison to 0.1.30 passed. Only two
  branch words and three title-stamp copies change; font bytes, all other
  resources and the 25 movie hashes (including lyrics) are identical.

## 0.1.30 - 2026-10-26 (local test build, not released)

- Corrects two HUD font startup calls that still used the linear uploader for
  0.1.29's swizzled 4x font. The user confirmed scrambled target names after a
  fresh boot. Both calls now use the existing dialogue-format upload routine.
- Preserves the 4x glyphs, English spacing, Japanese glyph cleanup, palettes,
  movie subtitles and both songs' lyrics. No mission script or logic changes.
- Adds instruction-level upload checks that reject the 0.1.29 path and verify
  both corrected paths. See `docs/hud_upload_0.1.30.md`. In-game confirmation
  remains required; this does not claim to fix mission 23.
- Final local ISO and scope checks passed: only the two executable calls and
  three title-version copies differ from 0.1.29. Fonts, mission resources and
  all 25 movies/lyrics are unchanged; Japanese-table inventory is zero.
  Output: `work/output/ACE-EN-0.1.30.iso`, SHA-256
  `f608d4e320e5d95506ed3f950640d99a6d371f69c0c0285d89adfb2a27d1efa0`.

## 0.1.29 - 2026-10-22

Credits correction: use the project lead's Discord nickname **pow** in the README
and published release acknowledgements. Game and patch files are unchanged.

Release packaging repair: adds `ACE-English-0.1.26-to-0.1.29.xdelta` so an existing
public 0.1.26 image can upgrade directly through Retro Trans. The initial release
provided only an original-disc patch, causing Latest to remain on 0.1.26.
The game image and original-disc patch remain unchanged. The 92,975,382-byte
upgrade passed a full round-trip check and public Latest/explicit/Next version route checks.
Catalog refresh run `39703037475` succeeded; all five uploaded assets passed size/hash checks.
`tools/add_release_upgrade.py` builds the additional route; future releases must
include and check an upgrade from the previous public version. Initial release
metadata is preserved under `docs/releases/0.1.29/initial-publication/`.

Published: https://github.com/retro-trans/ACE/releases/tag/v0.1.29.
The patch passed a full decode and output checksum comparison. Uploaded
assets match the local verified package; release evidence is in `docs/releases/0.1.29/`.
Retro Trans catalog refresh and public Latest/explicit-version routing checks passed.

Output: `work/output/ACE-EN-0.1.29.iso` (3,357,147,136 bytes), SHA-256
`02ad1831f30daf61348b24cdeb176e1be3bee019cfad7fefcac7a846844f7f6f`.

- Addresses corrupted speaker names and lock-on labels after the 4x HUD font expansion.
  Both 4x in-game fonts now share the original 1024x512 PSMT4 dialogue allocation.
  Changes the fixed HUD texture base to the dialogue base, while retaining separate palettes.
- Removes unused Japanese glyphs and unreferenced glyph records from in-game, menu and
  small-name fonts. Keeps English, full-width Latin letters/digits and required symbols.
  The main menu atlas shrinks from 1024x1024 to 1024x512; English screen metrics are preserved.
- Retains the 0.1.28 movie fade correction, all lyrics and mission dialogue. This is not
  a confirmed fix for the separate mission 23 completion report.
- Adds `tools/english_fonts.py` and `tools/verify_shared_fonts.py`; see
  `docs/shared_fonts_0.1.29.md`. Fresh-boot runtime confirmation is still required.
- Final resource comparison passed for all four in-game bundle copies and every changed
  menu/name font. English metrics, warning glyphs and HUD palette are preserved. All
  other game resources match 0.1.28 except title-version textures; the executable differs
  only at the intended GS-base word. All 25 movie hashes/lyrics match. Japanese-table
  inventory: 0 tables, 0 rows. DATA.BIN is 1,132,544 bytes smaller than 0.1.28.

## 0.1.28 - 2026-10-22 (local test build, not released)

Output: `work/output/ACE-EN-0.1.28.iso` (3,357,147,136 bytes), SHA-256
`c338b3476f280ac3658a592d389bedefb2733500b2960ca05e81091063be46c2`.

- Fixes Japanese lettering flashing before and after English in story movies. Extends all
  171 subtitle/title-card ranges across their faint fades in all 22 story movies.
- Measures English fade opacity on lettering rows, excluding the moving picture above
  the caption bar. Preserves corrected timing when subtitle specifications are regenerated.
- Keeps opening/ending lyrics, English mission dialogue, the 4x HUD font and prior fixes.
  The separate 0.1.27 mission 23 diagnostic is not incorporated; that issue remains unconfirmed.
- Adds frame-based timing refinement and encoded fade-edge checks. See `docs/movies.md`.
- All 22 rebuilt movies decode to their original frame counts. Checks across 5,849
  unique fade-edge frames found no remaining Japanese strokes above the verifier's
  compression tolerance. The reported clip's fade-in, fade-out and blank frames were
  visually checked in the encoded output. Emulator playback has not been performed.
- Final ISO comparison against 0.1.26 confirms unchanged gameplay resources, English
  mission dialogue, HUD font, opening/ending movies and other disc files. Only the
  title-version textures change outside the 22 corrected story movies. Japanese-table
  inventory: 0 tables, 0 rows.
- All 25 on-disc translated movies match their verified builds; packet positions and
  audio/nonvideo bytes match the Japanese original. Both lyric overlays are included.

## 0.1.27 - 2026-10-22 (local dialogue diagnostic, not released)

- Investigates a reported mission 23 completion stall on public 0.1.26. Cause remains
  unconfirmed; this build is not presented as a fix.
- Restores original Japanese dialogue only for internal mission 025 (campaign mission 23)
  and updates the title version. Keeps English objectives and all other release content.
- Adds `tools/mission_diagnostic.py` to generate and verify the narrowly scoped test ISO
  without changing translation sources. See `docs/mission23_investigation.md` for findings
  and the fresh-boot replay test. No gameplay reproduction was performed.
- Completed `ACE-EN-0.1.27-dialogue-diagnostic.iso` (3,357,147,136 bytes), SHA-256
  `7ba2521692255fc8aa7b518bf5e480340413e405d8e680f0ebdeff245c50205a`.
  Full byte comparison confirms all other ISO bytes are unchanged; four resource readbacks passed.

## 0.1.26 - 2026-10-21 (released)

Output: `work/output/ACE-EN-0.1.26.iso` (3,357,147,136 bytes), SHA-256
`95b7fafe2b4c5ddbfbd276f1322cb4cc08479891af0b714db3520b481472244c`.

- Published as `v0.1.26` with explicit user authorization. Includes opening/ending lyrics and all 22 restored
  story movies. Full patch round trip passed; all four uploaded asset sizes and SHA-256 digests match.
  Release: https://github.com/retro-trans/ACE/releases/tag/v0.1.26. Evidence: `docs/releases/0.1.26/`.
- Retro Trans catalog refresh succeeded; public Latest and explicit 0.1.26 routes select the verified patch.
- Fixes the repeated fragment beside `Resources` and stretched line after `Repair Eff.` on Launch Setting.
  Both headings now fit inside the fixed texture area in the launch and unit setup layouts.
- Preserves the complete wording, percentage symbol and other atlas labels. Retains the carrier-panel fix,
  all 22 translated story movies, lyrics, 4x HUD font and previous fixes.
- Encoded panel reconstructions, both meshes' UV checks and final ISO comparison passed. All three corrected
  texture copies and three title-version copies match. Other game resources and disc files, including movies
  and audio, match 0.1.25. Japanese-table inventory: 0 tables, 0 rows. In-game confirmation remains necessary.
  See `docs/launch_panel_0.1.26.md`.

## 0.1.25 - 2026-10-21 (local test build, not released)

Output: `work/output/ACE-EN-0.1.25.iso` (3,357,147,136 bytes), SHA-256
`4cf79a34ff43d8d1e0f166f69330352c3128d3f2d5a69f52ba012688f5137b7c`.

- Fixes the Rendezvous Point carrier-info panel: English text no longer crosses the stretched texture strip
  used for the value column. Removes split title/label endings and gray bars behind carrier/squad values.
- Uses `Carrier` and `Squad` for the two name labels. Keeps the complete `Carrier Info` heading and repair
  labels within the fixed-width left strip; the original heading is fully erased before narrower lettering.
- Leaves the left upgrade menu, panel mesh and dynamic values unchanged. Retains all 22 translated story
  movies, lyrics, 4x HUD font and prior fixes. See `docs/carrier_panel_0.1.25.md`.
- Reconstructed encoded panel and final ISO checks passed: both carrier-texture copies and all three title
  copies match. Other game resources, mesh, executable, movies, audio and other disc files match 0.1.24.
  The final Japanese-table inventory found 0 tables and 0 rows. In-game confirmation remains for testing.

## 0.1.24 - 2026-10-21 (local test build, not released)

Output: `work/output/ACE-EN-0.1.24.iso` (3,357,147,136 bytes), SHA-256
`afde085f60e6d04d3f83f0fa8dbbd4216d5155e9297541ca94eeca8b35f2cc89`.

- Restores English title cards and subtitles in all 22 story movies, including Gavlet Gablae's interview
  (`M1_MOVIE003`) reported by the user. Re-enables the existing translated movies and their saved specs.
- Retains opening/ending lyrics, the translated news/ending, 4x speaker font, prior fixes and title branding.
- Movie verification now requires 25 translated movies and checks all their original audio/nonvideo data;
  `--original-story` remains available for historical builds 0.1.16-0.1.23.
- All 25 on-disc movie hashes, packet positions and unchanged audio/nonvideo checks passed. All 22 restored
  story movies decode to their expected frame counts; the reported title and dialogue were visually checked.
- Comparison against 0.1.23 passed: game resources differ only in three title-version texture copies.
  The 4x HUD font, other disc files and the three opening/ending movies are unchanged. Both songs' 52 lyric
  rows pass layout checks. Japanese-table inventory: 0 tables, 0 rows.
- In-game playback and the 4x HUD allocation still need confirmation.

## 0.1.23 - 2026-10-21 (local test build, not released)

Output: `work/output/ACE-EN-0.1.23.iso` (3,357,147,136 bytes), SHA-256
`1410084f4bd46f00eb8dcd30d99f56555730d3e0758179c2c50b59672bbe2446`.

- Rebuilt the speaker-name/lock-on font at 4x resolution while preserving its on-screen size and spacing.
- Expanded its texture to 512x512, preserving the palette and original AREA OVER and other warning glyphs.
- Includes lyrics, all prior fixes and the automatic title version label. See `docs/hud_font_0.1.23.md`.
- Font and name-layout checks passed; expanded graphics-memory allocation requires gameplay confirmation.
- Final ISO comparison passed for all four HUD font copies. Only the HUD fonts and title version differ
  from 0.1.22; executable, dialogue and movies match. Japanese-table inventory: 0 tables, 0 rows.

## 0.1.22 - 2026-10-17 (local test build, not released)

Output: `work/output/ACE-EN-0.1.22.iso` (3,357,147,136 bytes; report `ACE-EN-0.1.22.json`, SHA-256
`2030fc1dddce477c80aa1b7692ad80164eefe4c3408e500dd6dddbc3807deb7d`).

- Added the build version and `github.com / retro-trans` at the bottom right of the title screen, matching
  the user's SRW Z reference: two small, right-aligned light lines with a dark outline.
- The version updates automatically from the build number. Extended the copyright sprite's right edge
  without moving or scaling the existing credits, and preserved all existing title artwork.
- Retains the 0.1.20 mission 3 fix, menu/HUD corrections, and opening/ending lyrics.
- Added title-layout previews and checks for unchanged artwork, executable, movies and unrelated game data.
  Final ISO comparison passed for all three title copies; Japanese-table inventory: 0 tables, 0 rows.
  See `docs/title_stamp_0.1.22.md`. In-game confirmation remains for user testing.

## 0.1.21 - 2026-10-16 (local movie variant, not released)

Output: `work/output/ACE-EN-0.1.21.iso` (3,357,147,136 bytes; report `ACE-EN-0.1.21.json`, SHA-256
`9ea4840758b1d6409c63af57520d15145c17d7bca21b172d14bbb22004e8082c`).

- Same game text as 0.1.20, including the mission 3 fix (confirmed in play).
- **Release movies leave out song-lyric overlays:**
  - `build.py --no-lyrics` (and `movie_text.py build MOVIE002 --no-lyrics`) drops the karaoke and lyric caption
    segments;
  - MOVIE002 keeps the English epilogue, staff credits and producer/publisher cards without karaoke;
  - MOVIE003 has only song lyrics and stays original;
  - MOVIE001 (news captions) is unchanged from 0.1.20.
  Local builds without the switch still include the user's lyrics.
- `package_release.py` takes `--version` and reads the expected output hash from the build report.
- Dialogue layout check: 3,493 rows, 0 problems. Final Japanese inventory: 0 tables.
- The user requested lyrics in the public release, so 0.1.20 is the selected release instead of this variant.

## 0.1.20 - 2026-10-16 (published)

Output: `work/output/ACE-EN-0.1.20.iso` (report `ACE-EN-0.1.20.json`, SHA-256
`45148f8c96a06d8cc5129de216dcf0f36830cb3f82f4f4f1c82652af79168082`).

- Selected for publication at the user's explicit request, with opening and ending lyrics/karaoke included.
- Includes the 0.1.18 difficulty/controller fixes and 0.1.19 restored HUD warnings.
- Release verification: all 3,493 dialogue rows pass layout checks; 0 Japanese text tables remain; all 35
  targeted UI textures are translated; all 52 karaoke rows pass. Three edited movies match 0.1.17 exactly,
  and all movie audio/nonvideo bytes and 22 story movies are unchanged from the original.
- The 320,364,671-byte release patch passed a complete decode-and-hash round trip. Candidate Retro Trans
  catalog routes passed. Manifest, checksums and evidence are under `docs/releases/0.1.20/`.
- Published [ACE English 0.1.20](https://github.com/retro-trans/ACE/releases/tag/v0.1.20) with lyrics included.
  All four uploaded asset sizes and SHA-256 digests matched the local package.
- Retro Trans catalog refresh `38926031385` succeeded; public Latest/0.1.20 routes, current-image no-op,
  and unknown-image rejection passed. Next version only selects the earlier 0.1.17 release as expected.

- **Mission 3 could not be finished:** the last Muzura sat at zero armour and never withdrew.
  - Cause: a 53-byte operator row spoken by an enemy speaker (row 21, with a `<cs(1)>` speaker colour). The
    colour code shares the operator message buffer, so the row overran it and the mission script stalled. The
    game did not crash.
  - Found by bisecting with diagnostic builds:
    - mission 3 in Japanese: retreat works;
    - dialogue only in Japanese: works;
    - rows 10-26: works;
    - rows 19-26: works;
    - rows 21-22: works;
    - row 21 alone: works.
  - Ruled out:
    - typing speed: scaling `<sp(n)>` to the Japanese typing time did not help (`build.py --scale-typing`
      remains as a diagnostic);
    - the lock-on labels;
    - the lines just before the retreat.
- **Rule:** operator rows with a `<cs(n)>` speaker are held to 46 visible bytes, the Japanese maximum for those
  rows. `dialogue_layout.py` enforces it, and 79 rows across 36 missions were shortened.

## 0.1.19 - 2026-10-16 (local test build, not released)

Output: `work/output/ACE-EN-0.1.19.iso` (3,357,147,136 bytes; report `ACE-EN-0.1.19.json`, SHA-256
`0cae3a989e87bb8b2fabb61bc058d185b2bfcb9a964fead4e8b0b0a6e28a232f`).

- Restored the original `AREA OVER` out-of-bounds warning by preserving its full-width English glyphs in
  the rebuilt HUD font. The same fix restores `CAUTION`, `ON AIR`, `MISSILE`, and `ERROR` in both HUD bundles.
- Kept original warning lettering, spacing and text; existing translated ASCII glyphs are unchanged.
  The 0.1.18 difficulty and controller fixes are included.
- Added a check for exact stock warning glyph pixels/metrics and a build comparison that permits only the
  two HUD font children in each HUD bundle to change. See `docs/hud_warning_0.1.19.md`.
- Verification passed: only HUD fonts changed from 0.1.18; other DATA.BIN resources, warning tables and
  executable are identical. Movie hashes match. ISO/UDF and payload checks passed, and the final Japanese
  inventory found 0 tables and 0 rows. In-game confirmation remains for user testing.

## 0.1.18 - 2026-10-16 (local test build, not released)

Output: `work/output/ACE-EN-0.1.18.iso` (3,357,147,136 bytes; report `ACE-EN-0.1.18.json`, SHA-256
`28712a4f103890cbb4a04f0c4743fef7e71cad3c98a5e0d1a8de21ad71b3151d`).

- Lowered Rookie, Pilot and Ace by five texture pixels to centre them vertically in their buttons, for both
  normal and highlighted states.
- Restored complete right-side labels in the Manual and Semi-Auto controller diagrams. Labels are drawn on
  the assembled panel, then split across the main and rotated continuation pieces used by the game.
- Added encoded-artwork previews and checks that only the four intended textures and their packed copies
  differ from 0.1.17. See `docs/menu_fixes_0.1.18.md`. In-game confirmation remains for user testing.
- Build and comparison passed: all three copies of each changed texture match the intended encoding;
  every other DATA.BIN resource and the executable are identical to 0.1.17. Movie hashes also match.
  ISO/UDF layout and rebuilt file hashes passed; all four encoded texture previews were visually reviewed.
  The final Japanese inventory found 0 tables and 0 rows containing Japanese.

## 0.1.17 - 2026-10-15 (published)

Output: `work/output/ACE-EN-0.1.17.iso` (report `ACE-EN-0.1.17.json`, SHA-256
`198bfe6cbd177347927aa412e716197f0d148e06ad768ee94537ac39b8e5871c`).

- Ending lyrics and karaoke now use a larger overlay across the bottom of the credits, as requested: 18 px
  romaji and 15 px English across a 470 px area, with a fading translucent dark backing.
- Replaced the Japanese text at the beginning of the ending with the existing English translation, scrolling
  over the restored background with the original motion. Removed the duplicate sentence subtitles.
- Kept the song words and timings from 0.1.16. All 52 opening/ending karaoke rows pass layout checks.
- The encoded epilogue passed all 1,920 frame checks with no surviving source lettering detected. Encoded
  samples were reviewed for readability, background restoration and the lyric overlay. The ending retains
  all 14,342 frames; a versioned preview is saved at `work/output/mp4/0.1.17/ending.mp4`.
- Final image checks passed: 0 Japanese text tables, 0 of the 35 original Japanese-lettered textures remaining,
  exactly three translated movies, all 22 story movies matching the originals, and unchanged movie audio and
  nonvideo bytes. ISO/UDF layout and rebuilt file hashes passed. Handoff and movie documentation updated.
- In-game playback remains for user testing.
- First public release packaging: ACE-3-style README and release notes, English-only source repository,
  and a Retro Trans Tools-compatible full xdelta patch with checksums and complete output verification.
  The project lead explicitly requested publication under `retro-trans/ACE` using `binhlt0402`.
- Published [ACE English 0.1.17](https://github.com/retro-trans/ACE/releases/tag/v0.1.17).
  The 320,312,789-byte patch passed a complete decode-and-hash round trip, and all uploaded assets matched
  their local sizes and checksums. Metadata and game-specific verification records are under
  `docs/releases/0.1.17/`.
- Retro Trans's scoped catalog refresh succeeded; public automatic-patching routes, already-current behavior
  and unknown-image rejection were verified.

## 0.1.16 - 2026-10-14 (local test build, not released)

Output: `work/output/ACE-EN-0.1.16.iso` (report `ACE-EN-0.1.16.json`, SHA-256
`d484a6c3b5b07806e442bd1656a75fd36c984bc17f9cbb5ac6864d031d4e70a3`).

- Added the user's supplied song lyrics as romaji karaoke with English translation: 31 sung rows for the
  Garnet Moon opening and 21 for the ending. The opening follows the shortened movie arrangement; ending
  lyrics wrap inside the left video strip to keep the translated credits clear.
- Paired English translations by meaning, preserved the supplied wording and kept translations spanning
  adjacent phrases visible continuously. Fixed alignment reading English rows as lyrics, macron handling,
  multiline highlighting and long lines being squeezed horizontally.
- Lyric changes now invalidate an older movie build. Lyrics stay in ignored local files; movie specs and
  timing/layout reports contain row indices rather than song text.
- Restores the original 22 MOVIE1 story cutscenes. Only MOVIE001, MOVIE002 and MOVIE003 receive movie changes;
  MOVIE005 stays original.
- Layout checks passed for all 52 sung rows. Dialogue (3,493 rows) and briefing (801 rows) checks passed.
  Listening and in-game checks of song timing, the ending and the title-screen transition remain for the user.
- Final text inventory: 0 Japanese text tables, 0 Japanese rows. Movie verification confirms the three expected
  replacements, all 22 original story movies and unchanged audio/nonvideo packets. The opening and ending
  retain 5,410 and 14,342 video frames respectively; MP4 previews are in `work/output/mp4/built/`.
- Texture verification: 35 Japanese-lettered original textures checked, 0 left in the built image. ISO/UDF
  layout and rebuilt file hashes also passed the builder's checks. Handoff and movie documentation updated.

## 0.1.15 - 2026-10-14 (local test build, not released)

Output: `work/output/ACE-EN-0.1.15.iso` (report `ACE-EN-0.1.15.json`, SHA-256
`d727eaa3e6a2bebecb5fbd443e7cfd1f2b05549bb369c46b5c05c88a51a2001d`).

- **Story movies:** a subtitle is now erased only where its lettering was (the pixels it covered, widened by 2 px).
  Before, a box over the whole card cut a thin black band into the bottom edge of the picture while a subtitle was
  shown. All 22 MOVIE1 movies are rebuilt.
- **Movie export:** `tools/movie_export.py` writes the disc's movies (originals, or the translated builds with
  `--built`) to MP4 (640x480 H.264 + the PCM soundtrack) in `work/output/mp4/`.

## 0.1.14 - 2026-10-14 (local test build, not released)

Output: `work/output/ACE-EN-0.1.14.iso` (report `ACE-EN-0.1.14.json`, SHA-256
`867ce41d66f19d4dd4055e31a3c12adb864dd72cb29c5fa208bb1b518e6aef5a`).

- **Leftover strings cleared:** the original mission containers carry unreferenced strings from earlier drafts of
  the dialogue in the padding between tables (for example a third variant of mission 6's "unexploded bomb" line).
  The game never shows them, but the build now clears them (11 gaps), so the mission containers hold no Japanese
  at all.
- **Confirmed in game (user playtest):**
  - mission 1, including the tutorial and the aerial combat that crashed 0.1.10;
  - mission 2's briefing, whose lines are the longest after the cut to the Japanese maxima;
  - the title screen, including the copyright lines;
  - the save screen, which shows the title "Another Century's Episode".
- **Remaining Japanese on the disc, none of it shown to players:**
  - parameter field names in `.def` files;
  - the internal unit table `CharGame.prm` (debug and test entries);
  - developer labels in event and motion scripts;
  - the debug test scene;
  - the story movies, which are not reviewed yet.

## 0.1.13 - 2026-10-14 (local test build, not released)

Output: `work/output/ACE-EN-0.1.13.iso` (report `ACE-EN-0.1.13.json`, SHA-256
`2bdf601cecf186afbe5c843a244281c4c3a6df328e3bf8815a16533b8f7540d4`).

### Every text held to a size the game is known to handle
Two in-mission buffers turned out to be sized for the Japanese, so every text whose buffer is not located is now
held to the Japanese maximum or to a length proven in play:
- **Briefings, debriefings and failure lines:** 89 visible bytes (Japanese maximum; before: 120, a guess). 201
  rows were shortened by three agents, with tokens and shared lines kept identical.
- **Briefing objective labels:** 39 bytes (Japanese maximum).
- **Main radio window:** 93 visible bytes, proven in play by mission 1 row 15; the Japanese maximum is 83. The
  132-byte buffer found in the code is not the only buffer, so the higher limit is not used. 6 rows were
  shortened.
- **Already within the Japanese maxima:** menus, help, hangar names, memory-card texts, lock-on labels, radio
  names and the encyclopedia.

## 0.1.12 - 2026-10-14 (local test build, not released)

Output: `work/output/ACE-EN-0.1.12.iso` (report `ACE-EN-0.1.12.json`, SHA-256
`4713e7cd548593a0c5614359cc101dab0dd6108639dc112e35689a3c4b1b35c7`).

### Crash fixes found in play (mission 1)
- **Operator window: one line, at most 54 bytes.**
  - **Freeze (0.1.8):** the small operator window (tutorials, operator calls) froze the game on a two-line
    message, mission 1 row 62. The Japanese never breaks a line there (2,477 rows).
  - **Crash (0.1.10):** a 57-byte message crashed PCSX2 (assertion "FQC = 0 on VIF FIFO READ"), mission 1
    row 69. A 56-byte message played fine, and the Japanese never exceeds 52 bytes.
  - Both were found by bisecting with diagnostic builds (`build.py --stock-missions/--stock-labels/--rows ...`).
  - `dialogue_layout.py` now knows which window each row is shown in and enforces both rules.
  - 119 rows were rewritten to one line and then 148 rows to 54 bytes, keeping duplicates identical.
- **Objective and failure labels** (rows 1-9 shown on the HUD) are held to the Japanese maximum of 28 bytes as a
  precaution. Their buffer is not located. 20 rows were shortened.

### Other fixes
- **Controller-setting screen:** the right-column labels no longer show doubled letters ("Descendd"). Each
  label's full English sits in the rotated strip the game draws over the panel, and the panel copy is now plain
  button background (t0302/t0303).
- **Ending credits:** ARTPRESTO uses the company's official spelling (0.1.9).
- **Story movies (MOVIE1, 22 cutscenes):** the subtitles and title cards are translated (`tools/subtitle_scan.py`,
  `tools/subtitle_spec.py`, `docs/subtitle_translator_brief.md`). They are included, but movies are not reviewed
  yet: a few fade frames per movie are still flagged by `tools/verify_no_japanese.py`.

### Still to test in game
- Mission 1 to the end, then mission 2's briefing. Its 107-109-byte lines test the briefing buffer, which is
  not located; the Japanese never exceeds 89 bytes.

## 0.1.8 - 2026-10-13 (local test build, not released)

Output: `work/output/ACE-EN-0.1.8.iso` (report `ACE-EN-0.1.8.json`, SHA-256
`3bb091625039765aa3251787cb31902b5b2746654d7c73b0ad838023da8af4a1`).

- **Staff names verified:** checked against MobyGames, IMDb and Wikipedia, and the kanji against an independent
  credit transcription. Corrected:
  - Suguru Ueda (was Masaru)
  - Hideo Emoto (was Aimoto)
  - Akira Takimoto (was Satoru)
  - Satoshi Otsuka (was Reiji)
  - Mitsuo Hasegawa
  - Naoizumi Tazo

  Four entries remain unconfirmed and are noted in the spec (`docs/movies.md`).
- **Ending layout:** the song credits no longer condense. A stray dash at the edge of the staff-roll panel (on
  four header lines) is now erased.
- **Checks:**
  - **Movies:** both final movies were viewed sample by sample: no Japanese.
  - **Executable:** the remaining Shift-JIS-looking byte runs were each confirmed as code or float data.
  - **Japanese inventory:** 0 tables.

## 0.1.7 - 2026-10-13 (local test build, not released)

Output: `work/output/ACE-EN-0.1.7.iso` (report `ACE-EN-0.1.7.json`, SHA-256
`b95a1de847436614dc00069ee1b2f64197905e434b2cecbbdfd5893f8227a6d3`).

### Japanese in the movies, the title screen and the executable
- **Movies** (`tools/movie_text.py`, `docs/movies.md`):
  - **Opening (MOVIE001):** the scrolling UCE statement is in English.
  - **Ending (MOVIE002):** the epilogue, the full staff roll (253 items), the producer cards, "Development" and
    the publisher card are in English.
  - **How:** the Japanese is erased against a reconstructed background, and English scrolls in its place with
    the same speed and fades.
  - **Splice:** only the GOPs that show text are re-encoded (83 + 638), fitted into the original bytes. Packs,
    audio and SCRs are unchanged, and the video PTS/DTS are rewritten. Each movie keeps its size and frame count.
  - MOVIE003 and MOVIE005 have no Japanese.
- **Staff names** are romanized. Readings not confirmed by an English source are marked in the spec; see
  `docs/glossary_decisions.md`.
- **Title screen:** the copyright lines read "©SUNRISE ©XEBEC / 1998 NADESICO Production Committee" and
  "©SOTSU AGENCY / SUNRISE".
- **Sortie screen:** the unit counter 機 reads "units".
- **Executable:** the 22 remaining internal labels are written in English in place: window-state names and two
  resource names. None is a lookup key.
- **No stale Japanese in the image:**
  - The build clears the strings of the 325 mission-container tables that the English copies replace.
  - It also zeroes the old DATA.BIN slot of every moved resource.
  - `tools/japanese_inventory.py` now scans every table, referenced or not, and finds none with Japanese.
- **Texture audit completed:** all 2,634 map, model and effect textures were viewed on contact sheets. None has
  Japanese.

### Still to test in game
- **Both movies:** playback, A/V sync around the re-encoded ranges, and the look of the English.

## 0.1.6 - 2026-10-13 (local test build, not released)

Output: `work/output/ACE-EN-0.1.6.iso` (report `ACE-EN-0.1.6.json`, SHA-256
`3c8bfd8ed4b22aa81d14387e0ad223e796a1ac0db6adc3a63bb0d5a3480d499e`).

### No Japanese text left
- `tools/japanese_inventory.py` finds **0 text tables with Japanese** in this image. The changes since 0.1.5:
  - the debug container InGame998 (five test strings) is translated;
  - three object lock-on labels referenced only from a container's extra table (Container, Chaff Grenade,
    Control Panel) are translated.
- **Baked-in lettering:** 35 menu and window textures carry Japanese in their pixels. All of them are relettered,
  249 labels in total, covering:
  - the hangar, carrier, tuning and part screens;
  - sortie and unit info;
  - mission info and results;
  - options, difficulty and time limits;
  - the pause and memory-card windows.

  Each texture keeps its size, format and palette, and the build replaces all 93 copies across the menu,
  briefing and window bundles (`docs/ui_and_textures.md`, brief `docs/texture_translator_brief.md`).
  - Vertical labels read bottom to top, like the game's own English ("SELECT").
  - New label terms with no established English: Ace Rating, Completion, Best Rating, Piloting, Escort Rate,
    Attack/Defense Acc., Hit Rate, Intrusions, Out of Area, Max Chain, Blind-Spot Hits, Target Damage.
  - The title screen's copyright line (Japanese company names) is unchanged on purpose.

### Still to test in game
- **Vertical labels:** that the game draws these quads unrotated, so the labels read bottom to top as in the
  Japanese.
- **t0803 "Ace Point Cost":** the bar is stored as two overlapping strips. The English sits in the first strip
  only.
- **t1202 radar labels:** these sat on a soft dark plate, which the erase removes. The English has only its
  drop shadow.

## 0.1.5 - 2026-10-13 (local test build, not released)

Output: `work/output/ACE-EN-0.1.5.iso` (report `ACE-EN-0.1.5.json`, SHA-256
`3f8440f80a93e957cc39533f50335d2dad81e1aaa3cb3d29b1f191d5dc5eb32b`).

### Menus, hangar and HUD text in English
- **Japanese inventory:** `tools/japanese_inventory.py` lists every text table still holding Japanese in an
  image. The remaining menu, hangar, memory-card, help and HUD tables were grouped by the font that draws them
  (`work/translation/en/ui/`) and translated with a shared brief (`docs/ui_translator_brief.md`).
- **Matched by content:** every copy of a table, wherever it lives, gets the same English. The 273 one-row
  lock-on label tables in the mission containers are appended and repointed.
- **Small fonts rebuilt:** f005 (hangar names, 2x) and the HUD font 50071 (radio names, lock-on, 1x) keep only
  the stock glyphs still in use and gain the English set; other codes draw '?'.
- **Executable and save icon:** the title string and the placeholder name are English (same-size patches),
  and the memory-card browser title in `icon.sys` reads "Another Century's Episode".
- See `docs/ui_and_textures.md`.

## 0.1.4 - 2026-10-13 (local test build, not released)

Output: `work/output/ACE-EN-0.1.4.iso` (report `ACE-EN-0.1.4.json`, SHA-256
`f90dd7cf31f34d30333849aa3ea1c18bb2a2ceb3488645adebf401d659d5050e`). 0.1.3
(`529fc1fa...a6d51`) was the same build without the briefings.

### All story dialogue in English
- **In-mission dialogue complete:** all 45 story missions, the alternate Mission 32 script (InGame090) and the
  extra-mission objectives. That is 3,488 rows, of which 3,230 carry visible text and the rest are timing-only
  rows kept byte for byte. Translators worked mission by mission in story order with a shared brief
  (`docs/dialogue_translator_brief.md`); every row was examined and 0 layout problems remain. Only the debug
  container InGame998 (five garbled test strings) stays Japanese.
- **Briefings, debriefings, mission names, objective labels and failure lines complete:** 801 rows in 47 menu
  tables (f001-f081), in all three copies (standalone, MenuCampaign, MenuFree).
  - Mid-text tokens (`<cs()>...<ce()>`, `<pic()>`, `<mk()>`, `<ar()>`, `<pt()>`) are kept in their original
    order; the build rejects any row whose token sequence differs.
  - Limits: names 1 line, 200 units, 27 bytes; objectives 2 lines of 200 units, 60 bytes; text 2 lines of 440
    units, 120 bytes. The briefing buffer size is not located, so 120 is a test value (the Japanese maximum
    is 89).
- **Consistency passes:**
  - Stock radio lines and operator-slot barks that repeat across missions were unified to their majority
    rendering (69 rows).
  - Repeated failure lines and objective labels in the briefings were unified (23 rows).
- **Glossary grew with each mission.** New decisions:
  - Jonathan Green (akurasu, replacing "Glenn"), Blue Hawk of Giganos, Gea Garing, Jamitov Hymem, Le Cain and
    Hime Utsunomiya.
  - Kahns is locked as an unsourced romanization.
  - Five mission names were shortened to fit the name field.
  - See `docs/glossary_decisions.md`.
- **Speakers** are not stored in the game data. Each row's inferred speaker is recorded in the working files, with
  `?` where the scene does not settle it.
- DATA.BIN grows 4.2 MB, absorbed by the disc padding; the image size is unchanged.

### Still to test in game
- The briefing screen with English text (byte limit and token timing), the mission-select names, the
  objective labels in the narrow box, and the in-mission window with all missions.

## 0.1.2 - 2026-10-13 (local test build, not released)

Output: `work/output/ACE-EN-0.1.2.iso` (report `ACE-EN-0.1.2.json`, SHA-256
`faa7e7f9b30af6915d1c240d69dbef3e9d80ecc0c527f5469cf43b02c9adcf41`).

### In-mission dialogue: pipeline and first five missions
- Translated all in-mission rows (objectives and radio dialogue) of InGame 001-005 (268 rows). In story order
  these are missions 1-4 and 29 (Sanc Kingdom Defense); InGame numbers are design ids (map in
  `work/glossary/mission_order.json`). Four translators; every row examined, 0 layout problems.
- Each mission container gets an English copy of its main text table, and its table pointer (word 20) is
  redirected; the original table is untouched. Tokens (`<op()> <sp(20)> <ab(1000)>`...) are re-attached
  automatically, and timing-only rows are kept byte for byte.
- Limits found in the executable: 132-byte typed-text buffer per row with no bounds check (EE 0x2366e0,
  0x237af8). Rows are held to 128 visible bytes, 2 lines and 400 units. The longest English row uses 98 bytes.
- Dialogue font (resource 50070/50050 in Fe1p.bnd and Fe2p.bnd, two copies each) gets the English set at
  **2 texels per unit**. 3x and 4x do not fit while all Japanese glyphs are kept for the untranslated missions;
  4x is planned once dialogue is complete. Each Fe bundle grows 2,144 bytes (font records).
- Added GS-swizzle (PSMT4 as PSMCT32) support to the font tools. Its round trip is byte-exact on the stock atlas.
- Speakers are not stored in the data. Translators infer them and record a `speaker` field; uncertain ones are
  marked `?`.
- Names added: Bright Noa, the rank conventions (大尉 Lieutenant, 大佐 Captain) and operator-slot conventions.
- Not translated yet: lock-on unit labels (13px HUD font, no Latin), briefings and debriefings (menu tables
  f001-f050), and the other 40 missions.
- Not yet tested in game. Watch the dialogue window text, line breaks and the Fe bundle growth.

## 0.1.1 - 2026-10-13 (local test build, not released)

Output: `work/output/ACE-EN-0.1.1.iso` (report `ACE-EN-0.1.1.json`, SHA-256
`9692aef91842d66de82d0ce41b47fd79ca050863490a84f05c1ae25dd9cfb523`).

- English menu font is now HD: the 95 English glyphs are stored at 4x resolution (88-texel cells, 4 texels per
  screen unit). They are sharp when the emulator renders above native resolution. Confirmed from the glyph
  renderer (EE 0x1c8bd8-0x1c8ce8) that sprite size comes from the metrics and texture coordinates from the UVs,
  so no executable change is needed.
- Anti-aliasing ramp widened from 5 to 16 alpha levels using the 11 unused palette entries; stock entries are
  unchanged.
- Fixed `j`: its left overhang was clipped in 0.1.0; it now uses a negative bearing. Found that the renderer
  moves the pen by bearing + advance, and text measurement now follows that.
- Metrics, wrapping and pagination are unchanged (161 encyclopedia pages, 0 layout problems). Glyphs occupy
  atlas rows 576-934 in all eight f010 copies.
- The HD texels compress less well: MenuTitle, MenuIntro, MenuTitleIntro and MenuEnding no longer fit their
  original slots and are appended to DATA.BIN (+1.5 MB, inside the disc padding; image size unchanged).
- Not yet tested in game. Native-resolution appearance (real hardware or 1x emulation) needs a look.

## 0.1.0 - 2026-10-13 (local test build, not released)

Output: `work/output/ACE-EN-0.1.0.iso` (build report `ACE-EN-0.1.0.json`, SHA-256
`bc55924562839ce608864617e689c8c17f71c45e19381308eea0e708c5c6f404`). Source: Another Century's Episode (Japan),
SLPS-25394.

### Variable-width English font
- Found that the menu text renderer is already proportional: each CCM glyph record carries its own width and
  advance. No executable change was needed.
- Added a complete printable-ASCII set (95 glyphs, Noto Sans JP, weight 340, about 8 units average advance) to
  all eight copies of the main menu font f010 (standalone and the seven `Menu*.csc` bundles). Glyphs go in empty
  atlas rows 576-598 and use the font's own five-level alpha palette. Original glyph records and pixels are
  unchanged and verified by the build.
- Remapped fullwidth ０-９ to the new digits, because the widget copy routine (EE 0x212040) turns every ASCII
  digit into its fullwidth code.
- See `docs/vwf.md`. Fonts f005 (unit names), f001 (button help) and f015 (large digits) are not patched yet.

### Terminology database (encyclopedia), fully translated
- All 88 titles and 142 Japanese pages are translated (three translators, about 80 rows each; 230 of 230 rows
  examined). They are wrapped at 440 units and paginated to at most 8 lines and 390 bytes per page, which gives
  161 game pages. The game counts pages at run time (EE 0x2760d0), so long entries continue on extra page ids.
- Names follow akurasu.net (ACE Mech Database, SRW character lists) and the SRW MX glossary; overrides are in
  `docs/glossary_decisions.md`. Long akurasu mech names are shortened only in the 27-byte title list (for
  example "MP Gespenst Mk-II"); the full name opens the description.
- The `#c[FF0000]`...`#c` pairs are dropped from the English. All 155 occurrences on the disc wrap only a line
  break and colour no visible text.
- Mech stat blocks use one house format: "Pilot:", "Height: ... Weight: ...", "Series:".

### Build pipeline
- New tools: `ace_formats.py` (BND, CSC LZSS, FMG, CCM, TM2, ISO), `vwf_font.py`, `encyclopedia_source.py`,
  `encyclopedia_layout.py`, `akurasu_terms.py`, `merge_slices.py`, `strip_jp.py`, `build.py`.
- The LZSS packer uses lazy matching and comes out smaller than the original compressor, so all seven rebuilt
  menu bundles fit back in their original DATA.BIN slots. Only the standalone f010.ccm and f205.fmg are appended
  (DATA.BIN +84 KB).
- The ISO keeps its original file order and size. The 22 files after DATA.BIN shift into the disc's trailing
  padding, with ISO9660 (both byte orders) and UDF file entries rewritten and verified. The game opens files by
  name (CdSearchFile).

### Not verified
- Not yet tested in game or an emulator. Checked offline: structure, round trips, payload hashes, glyph coverage,
  and line, page and byte limits. Proofs are in `work/ui/vwf/` and `work/ui/encyclopedia/`.
- The encyclopedia body widget's exact buffer capacity was not located; pages stay within the largest Japanese
  page (391 bytes).
- The menu bundles grow by up to about 4 KB decompressed (MenuCampaign: 7,512,128 to 7,516,160 bytes).
