# Changelog

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
