# Movies (MOVIE0/*.PSS)

## Current scope: 0.1.24

On 2026-10-21 the user requested restoring all 22 translated story cutscenes. Their existing specs and
English-only copies are active again directly under `work/translation/en/movies/`. Cached translated PSS
files match those specifications. The older exclusion described in the historical sections below no longer
applies. All three MOVIE0 translations, including the selected ending overlay and both songs, remain active.
MOVIE005 stays original. Build without `--movies` to include all 25 active specs:

```text
python tools/build.py 0.1.24
python tools/build.py 0.1.24 --write
python tools/verify_movie_scope.py work/output/ACE-EN-0.1.24.iso
python tools/verify_story_restore.py work/output/ACE-EN-0.1.24.iso --write
```

The verifier checks all 25 movie hashes, packet positions and unchanged audio/nonvideo bytes. When verifying
historical builds 0.1.16-0.1.23, add `--original-story` to the old verification commands below.
`verify_story_restore.py` compares game resources against 0.1.23, allowing only the automatic title-version
texture update. It also requires identical opening/ending movie hashes and unchanged other disc files.

The MOVIE0 directory has four FMV movies (MPEG-2 video at 512x448, 29.97 fps, plus 16-bit PCM audio in private
stream 1). MOVIE1 contains another 22 story cutscenes.
Every frame was sampled every 2 seconds and checked:

| Movie | Content | Japanese |
| --- | --- | --- |
| MOVIE001 | Opening: the refugee fleet attack, then a UCE statement | the statement (about 50 s of scrolling text) |
| MOVIE002 | Ending: epilogue, staff roll, producer cards | epilogue, full staff roll, producer cards, "開発", "販売" |
| MOVIE003, MOVIE005 | Attract/intro movies | none ("powered by FROMSOFTWARE" only) |

## How the text is replaced (tools/movie_text.py)

All the Japanese scrolls upward at a constant speed, so each segment is described by its frame range, its speed
and the block row of every line (`work/translation/en/movies/<movie>.json`).

1. **Analysis.** Each frame's difference from the clean background is shifted by the scroll offset and
   max-accumulated into one tall image of the whole text block (`work/ui/movies/<movie>_<k>_block.png`). This
   gives the exact rows and x span of every Japanese line, and the erase mask.
2. **Background.** For a still (the opening statement, the epilogue) it is the per-pixel median of the still,
   scaled per frame to follow fades. The staff roll sits on a black panel beside a video column, so the erase is
   limited to the panel. The producer cards scroll over a live shot with a moving lens flare: there the background
   is the per-pixel median of the neighbouring 61 frames, taken only at times the text does not cover the pixel.
   The one card that does not scroll ("― 販売 ―" above the BANPRESTO logo) sits on a still part of the shot. Its
   area is restored from the frames just before and after it, and the English follows its fade.
3. **English.** It is drawn in Noto Sans at the Japanese lines' rows. It uses the same scroll (sub-pixel), the same
   top and bottom fades, the measured lettering colour and a 1 px shadow. Names in two-column lists are condensed
   to their column when needed.
4. **Splice.** Only the GOPs that show text are re-encoded. Each is encoded as a closed GOP of the same frames with
   ffmpeg's mpeg2video and the stream's own inter matrix, and ffmpeg's sequence header is dropped. The GOP is fitted
   into the original GOP's bytes (lowest qscale that fits, padded with zero stuffing). Each picture starts in a
   video packet of its own, as in the original. Packs, audio packets and SCRs are untouched. The PTS/DTS of the
   video packets in the changed range are rewritten for the pictures that now start in them
   (PTS = 3877 + 3003 x display index, DTS = 874 + 3003 x decode index, anchors only).
5. **Checks.** The rebuilt PSS has the same size and packet layout, carries exactly the new elementary stream, and
   decodes to the original frame count. `build.py` streams it into the image and verifies it on the disc.

    python tools/movie_text.py analyze MOVIE002           # block images + line bands
    python tools/movie_text.py preview MOVIE002 6900      # before | after frame in work/ui/movies/
    python tools/movie_text.py build MOVIE002             # work/output/movies/MOVIE002.PSS (+ .json report)

`build.py` takes every movie with a spec and fails if its build is missing or older than the spec.

## Wording

- 統一地球暦 is rendered "Unified Earth Calendar" (no established English; see `docs/glossary_decisions.md`).
- The UCE's Japanese name 地球統一機構, shown in brackets under "UCE -United Community of the Earth-", is rendered
  "(Earth Unification Organization)".

### Staff names

Role titles are translated; names are romanized (given name first). Readings were checked against MobyGames,
Wikipedia, IMDb and other English credits; the kanji were cross-checked with an independent transcription of the
credits (raido.moe), which agrees with the video everywhere except one name where the video clearly shows 皇士
(kept). Four entries remain unconfirmed and carry a `note` in the spec: 長谷川 三及 (Mitsuo Hasegawa, MobyGames
only), 田雑 直泉 (Naoizumi Tazo, given name unconfirmed) and the company names ライツ・イン (Rights In) and
アートプレスト (Artprest). Logos (N.O.Y.B., avex trax, BANPRESTO, FROM SOFTWARE, the A.C.E. logo) and the English
lines ("BURNING PRODUCTION", "UCE -United Community of the Earth-", "END") are kept as they are.

### Verification of the original scroll replacements

The earlier scroll replacements were sampled every 240 frames (opening) and every 180 frames (staff roll; less
than one screen height of scroll, so every line appears in at least two samples). This check predates the decision
to preserve the ending's Japanese epilogue scroll and restore the original story cutscenes.

## Karaoke and movie scope for 0.1.16

The user supplied the opening and ending lyrics. Their text stays in the ignored
`work/translation/en/movies/lyrics/` folder; movie specs contain row indices, display settings and timings only.
The supplied English wording is preserved. `*.provided.txt` files retain the original two-block inputs.

- **MOVIE001:** English news captions and the translated scrolling statement.
- **MOVIE002:** the original Japanese epilogue scroll with English sentence captions, translated staff and
  producer credits, and 21 rows of song karaoke. Lyrics wrap inside x=35..210 at the foot of the left video strip
  (13 px romaji, 11 px English); this also leaves the later producer and logo cards clear.
- **MOVIE003:** Garnet Moon karaoke, 17 px romaji and 14 px English at the bottom. The movie arrangement uses 31
  of the supplied 38 romaji rows; rows 26..32 (zero based) are omitted. Sung phrases run approximately
  42.58..171.34 seconds, correcting the earlier estimate of a 60-second vocal start.
- **MOVIE005 and all 22 MOVIE1 files:** original disc content. Disabled story specs stay in
  `work/translation/en/movies/disabled/`.

English phrases are paired by meaning, not by relative line counts. A translation spanning adjacent romaji rows
stays visible continuously. Gold highlighting follows word timing across wrapped lines and completes before the
line fades. Audio, pack headers, movie byte lengths and frame counts are preserved.

### Rebuilding and checking

`tools/lyrics.py` reads `romaji || English` pairs. It rejects ambiguous two-block files until their lines have
been paired. `prepare_song_pairs.py` performs the reviewed row mapping for these particular supplied files;
its source contains only row numbers. Do not run that mapping on different lyrics without reviewing it.

`whisper_tool.py align`, run with the 64-bit Whisper environment, aligns romaji only. It accepts `--from`, `--to`
and `--rows` for difficult passages, handles macrons and stores numeric timing evidence, not a song transcript.
`finalize_song_timing.py` combines the successful local alignment windows. The resulting timing is automatic:
numerical sequence, phrase coverage and screenshots have been checked, but listening and in-game review remain.

```text
python tools/finalize_song_timing.py
python tools/karaoke_spec.py MOVIE003
python tools/karaoke_spec.py MOVIE002 --layout strip
python tools/verify_karaoke.py
python tools/movie_text.py build MOVIE003
python tools/movie_text.py build MOVIE002
python tools/movie_export.py --built MOVIE002 MOVIE003
python tools/build.py 0.1.16 --write --movies MOVIE001,MOVIE002,MOVIE003
python tools/japanese_inventory.py work/output/ACE-EN-0.1.16.iso
python tools/verify_no_japanese.py work/output/ACE-EN-0.1.16.iso --textures-only
python tools/verify_movie_scope.py work/output/ACE-EN-0.1.16.iso
```

The movie freshness hash includes the external lyrics file, so changing a lyric invalidates an old movie build.
Layout reports in `work/ui/movies/karaoke/*.layout.json` check every row's bounds, translation coverage, timing
order, completed highlight and credit clearance. Timing evidence is saved alongside them. Before/after previews
are in `work/ui/movies/MOVIE00N_*.png`; encoded preview frames use the `karaoke/` subfolder.

`verify_movie_scope.py` checks that exactly MOVIE001/002/003 were replaced on disc, all 22 story movies match the
source byte for byte, and all nonvideo data in the three replaced movies (including every audio packet) is
unchanged. The old movie portion of `verify_no_japanese.py` assumes that every segment erases Japanese text;
it does not support additive captions or karaoke. Use its `--textures-only` check for textures, the text inventory
for game text and the scope/layout/frame-count checks above for this build.

### Completed build verification

`work/output/ACE-EN-0.1.16.iso` was built on 2026-10-14. SHA-256:
`d484a6c3b5b07806e442bd1656a75fd36c984bc17f9cbb5ac6864d031d4e70a3`.
The final inventory found 0 Japanese text tables; the texture scan found 0 of the 35 original Japanese-lettered
textures. All 52 karaoke layouts passed. PSS and MP4 frame counts are 5,410 for the opening and 14,342 for the
ending, matching the originals. Encoded frames were visually inspected for wrapping, highlight and credit
clearance. Movie scope and unchanged audio/nonvideo bytes passed
`work/output/ACE-EN-0.1.16.movies.verify.json`; texture results are in the adjacent `.textures.verify.json`.
Listening review and a game playtest remain outstanding.

## Ending revision for 0.1.17

On 2026-10-15 the user selected a larger lyric overlay across the bottom of the credits and requested direct
replacement of the Japanese text at the beginning of the ending.

- `karaoke_spec.py MOVIE002 --layout overlay` sets 18 px romaji and 15 px English across 470 px, ending at
  y=432. A translucent dark backing covers the lyric area, fading at its upper edge and with each lyric cue.
  Credits scroll behind it. The supplied song words and timings are unchanged.
- `epilogue_spec.py` uses the existing translation in `movies/captions/MOVIE002.json` as source text for nine
  paragraphs / 20 English lines. That file is now a reference, not an active sentence subtitle track.
  The source Japanese is erased against the reconstructed still background, with the English following its
  upward motion and edge fades. The separate sentence subtitles are removed.
- `verify_epilogue.py` checks all 1,920 frames in the replaced epilogue interval for surviving source lettering,
  excluding the new English. Its report is `work/ui/movies/epilogue.verify.json`.

Rebuild the ending with these commands before making the new disc:

```text
python tools/epilogue_spec.py
python tools/karaoke_spec.py MOVIE002 --layout overlay
python tools/verify_karaoke.py
python tools/movie_text.py build MOVIE002
python tools/verify_epilogue.py
python tools/movie_export.py --built MOVIE002
python tools/build.py 0.1.17 --write --movies MOVIE001,MOVIE002,MOVIE003
```

Use the final inventory, texture and movie-scope commands above with version 0.1.17. The previous 0.1.16
section documents the older layout; `overlay` is now the selected ending layout.

The encoded epilogue passed all 1,920 frame checks with zero failing frames and a worst surviving source-stroke
share of 0.0. Encoded preview frames are saved in `work/ui/movies/0.1.17/`; the versioned MP4 is
`work/output/mp4/0.1.17/ending.mp4`. The ending movie retains all 14,342 source frames.

Completed image: `work/output/ACE-EN-0.1.17.iso`, SHA-256
`198bfe6cbd177347927aa412e716197f0d148e06ad768ee94537ac39b8e5871c`.
The final scans found 0 Japanese text tables and 0 of the 35 original Japanese-lettered textures. Movie scope,
all 22 original story movie hashes, unchanged movie audio/nonvideo data, and the builder's ISO/UDF and payload
checks passed. Verification reports are saved beside the ISO. In-game playback still needs user testing.
