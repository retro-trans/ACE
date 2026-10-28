# 0.1.33 runtime story-movie subtitles

Local test build, requested by pow on 2026-10-27. Not a public release.

## Behavior

All 22 MOVIE1 story files are restored byte-for-byte from the original disc.
The game applies 148 English bottom-bar captions and 23 title cards to decoded
pictures in memory. Their corrected frame ranges, fade timing, wording and
4x-antialiased font rendering come from the existing English movie specs.
The opening/news, ending/credits and opening-song replacements remain unchanged,
including all English lyrics and romaji karaoke. No translation is removed.

The overlay erases the original lettering and its faint fringes, rather than
covering a large rectangle that could touch the moving picture. Each caption's
mask is compiled from the existing original-frame analysis. Antialiased English
pixels and the mask are stored as a compact byte stream. There is no new video
encoding, no additional video quality loss, and no gameplay font dependency.

## Implementation

- `tools/movie_overlay.py` compiles a 1,522,944-byte payload containing the
  renderer, movie directory, pixel streams and per-picture fade tables.
- The movie-open prologue at EE `0x2001a0` selects the story movie and resets
  its picture counter. MOVIE0 and unknown movie IDs disable the overlay.
- The successful decode path at `0x1f24c0` calls the overlay before the original
  queue-publication function `0x1f2e10`. It writes only to the producer buffer,
  through the same uncached alias used by the decoder. A memory barrier precedes
  publication. Neither ring bookkeeping nor GS/DMA commands are changed.
- The counter advances once per successfully decoded/queued picture, not per
  display tick. Captions therefore travel with the pictures during stalls,
  repeats or skips. Reopening a movie resets timing. Negative decode results
  bypass the hook through the original error path.
- RGB32 storage consists of 16x16 blocks, ordered by block column, then block
  row. This was checked against the actual movie ring in the supplied ending
  save state; its alpha bytes are `0x80`. Runtime guards require 512x448 and
  the original two-picture ring. There is no separate font texture allocation.
- The original empty second ELF load segment becomes a real executable/data
  segment at `0x34a480`, after the original BSS. Original BSS clearing still
  ends there. Startup heap setup, both heap-bound helpers and libc's sbrk cursor
  move to `0x4be180`, beyond the payload. No live heap space is used as a cave.
- `build.py` now permits executable growth, updating ISO9660 and UDF extents
  and verifying the complete executable readback. Other replacement files
  retain their existing size rules. The overall ISO size remains unchanged.

The payload costs about 1.45 MiB of EE RAM. Real playback and gameplay memory
headroom still need fresh-boot testing; a CPU harness cannot establish these.
The feature is explicitly selected with `--movie-overlay` while under test.

## Verification and reproduction

```text
python tools/build.py 0.1.33 --movie-overlay --write
python tools/verify_movie_overlay.py --iso work/output/ACE-EN-0.1.33.iso
python tools/verify_movie_scope.py work/output/ACE-EN-0.1.33.iso
python tools/verify_story_restore.py work/output/ACE-EN-0.1.33.iso --baseline 0.1.32 --write
```

The overlay verifier runs the actual patched instructions in a MIPS64 CPU,
including both original callsites and delay slots. It checks every caption's
boundaries, midpoint and full-opacity point; the other video buffer, outside
pixels, guard regions, callee-saved registers, queue arguments and ring
bookkeeping must remain unchanged. It also checks all movie resets, excludes
opening/ending movies, rejects unsupported dimensions and producer indices,
and verifies all heap boundaries and the unchanged BSS clear range.

Compiled masks, glyph antialiasing and fades are checked against the English
specs and original-frame analysis. Preview images are produced by the same
machine code running against original decoded frames, not by image editing.
Evidence is under `work/ui/movie-overlay/`; generated payload and its English
manifest are under `work/output/movie-overlay/`.

Completed checks: 953 machine-code frame cases across all 171 cards, 51
movie-state cases, and 437,190,656 framebuffer-pixel comparisons pass. The
finished ISO passes original-story movie hashes, unchanged opening/ending
hashes and soundtracks, ISO9660/UDF layout checks, and comparison with 0.1.32:
only the intended executable patch and three title-stamp resources differ
outside the restored story movies. Fonts, dialogue and other game data match.

Local ISO: `work/output/ACE-EN-0.1.33.iso`, 3,357,147,136 bytes, SHA-256
`62f705bc67ae40539f8147ce4209f93617f17e725ebee389882568133acdc8c0`.

CPU verification is not emulator playback confirmation. Use a fresh boot of
the local ISO and a normal memory-card save; older save states contain the old
executable and heap layout. Check an early story title, the M1_MOVIE011 scene
previously reported for Japanese flashes, movie skipping/replay, and entering
gameplay. Desktop controls have not been used.

## Patch-size comparison

The local patch was encoded and decoded with the pinned Retro Trans Tools
xdelta engine using the same default settings as the public 0.1.32 patch.
Full reconstruction matches the ISO hash above. Original-disc patch sizes:

| Build | Bytes | Decimal MB |
| --- | ---: | ---: |
| Public 0.1.32 | 890,566,740 | 890.6 |
| Local 0.1.33 | 319,280,205 | 319.3 |
| Reduction | 571,286,535 | 571.3 |

The patch is **64.15% smaller**. Local artifact:
`work/output/ACE-English-0.1.33-local.xdelta`, SHA-256
`a3d714b6ecda2309e5189da54ef766075f74cf73cbe50ca08a8d092d5f239818`.
This patch requires the original Japanese ISO, not a previous English build.
Evidence: `work/ui/movie-overlay/patch-size-0.1.33.json`.
Public assets and catalog entries are unchanged; no release has been requested
for this build.
