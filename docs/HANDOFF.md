# Handoff: Another Century's Episode English fan translation

Project root `E:\Projects\ACE`. Read `AGENTS.md` first: it holds the folder layout and the rules (versioning,
changelog, akurasu as the term source, no Japanese script in git, **no GitHub release without an explicit
request**, releases must work with Retro Trans Tools). The user explicitly requested repository creation and
release 0.1.17 on 2026-10-15, using `binhlt0402` in `retro-trans`. Repository: https://github.com/retro-trans/ACE.
Packaging and publication instructions are in `docs/RELEASING.md`.

## Public release

The user explicitly requested a new release on 2026-10-16 and confirmed that lyrics must be included.
The selected image is **0.1.20**, SHA-256
`45148f8c96a06d8cc5129de216dcf0f36830cb3f82f4f4f1c82652af79168082`.
It includes the play-confirmed mission 3 progression fix, the 0.1.18 menu fixes, the restored HUD warnings,
and both opening/ending lyric overlays. The lyric-free 0.1.21 image is a local variant and is not selected
for publication. Release notes: `docs/releases/RELEASE_NOTES_0.1.20.md`.

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
No release was requested for this build. The public release remains 0.1.17.

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
- **The 22 story cutscenes (`/MOVIE1`):** the user wants no baked translation. Their specs are parked in
  `work/translation/en/movies/disabled/`. Build 0.1.16 restores all 22 original movies; 0.1.15 contained the
  earlier subtitled versions. `verify_movie_scope.py` checks the restored files against the original ISO.

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
