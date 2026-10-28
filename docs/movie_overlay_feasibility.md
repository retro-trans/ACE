# Movie overlays and patch-size investigation

Implementation follow-up: see `docs/movie_overlay_0.1.33.md`. The notes below
record the initial feasibility investigation, before the overlay was built.

2026-10-27. Local investigation against public 0.1.32; no new game build or
release. The requested outcome is a smaller original-disc patch with all
translations and lyrics retained and no loss of video quality.

## Compression result

The published full patch is 890,566,740 bytes. Re-encoding with the Retro Trans
Tools bundled xdelta3 3.2.0 at level 9, a 128 MiB source window and a 32 MiB
input window produces 887,030,447 bytes: 3,536,293 bytes (0.397%) smaller.
The published patch already uses LZMA secondary compression. Its compressed
replacement-data sections total 875,999,070 bytes; matching instructions and
addresses are a comparatively small part of the download.

The compact patch was decoded with Retro Trans Tools and the entire resulting
ISO verified against public 0.1.32: SHA-256
`72d807e7b9e8f02f54b2ff3f491ed0fdb60c4cbf15dabdb81a0195217b248f73`,
3,357,147,136 bytes. All videos, text and lyrics are therefore identical.
Evidence: `work/ui/patch-size/compact-0.1.32.json`.
Local artifact: `work/output/ACE-English-0.1.32-compact.xdelta`.
It is an experiment, not a replacement published asset or catalog entry.

## Runtime subtitle approach

The existing English story-movie timing files contain 148 bottom-bar captions
and 23 title cards across 22 movies. Their combined JSON size is only 77,341
bytes. A runtime renderer could retain original movie bytes, draw an opaque
black rectangle over the baked Japanese text, and draw the timed English text
above it. Black-background title cards can use the same principle.

Preserve the corrected faint-fade coverage in the existing `frames` and
`scan_frames` metadata. English alone is insufficient: the Japanese must be
masked from its first visible frame through its last visible frame.

This is a promising design, not an implemented or runtime-tested feature.
Text over moving scenery and scrolling credits needs separate treatment.
An initial implementation could retain the current opening/news/ending movie
replacements, including karaoke and English lyrics, while converting the 22
story movies. No credible final patch-size estimate exists until that build
is generated; modified movie-region totals are not delta-patch savings.

## Offline reverse-engineering leads

Original executable mapping: file offset = EE address - 0x100000 + 0x80.
The disassembly has inaccurate decoding of some PS2 instructions; inspect raw
words before modifying code. Addresses below are leads, not validated hooks.

- Movie opening routine at 0x2001a0 formats the disc movie path using the
  pointer at 0x2c92b8 to the format string at 0x2c46b0. Capture movie identity
  here if implementing a renderer.
- Movie state block is at 0x33b100; state is at 0x33b118. The setup routine at
  0x200270 prepares two buffers and transitions from state 2 to state 3.
- The state-3 update at 0x2003a0 checks stop/skip conditions through 0x200a30,
  calls the player update wrapper 0x1f2f30, and tears down through 0x200aa0.
- Routine 0x200430 checks picture availability through 0x1f2fc0, selects a
  buffer through 0x1f2fb0, appends a packet referencing that buffer, and calls
  0x1f2fa0. These wrappers lead to 0x1f06e0, 0x1f06b0 and 0x1f0680.
- Callback 0x200950 services movie data reads; it is not a proven subtitle
  presentation hook.

Still required: identify the displayed picture clock, establish overlay draw
ordering and GS state restoration, reserve font texture/packet memory safely,
and handle restart, skip and playback stalls without timing drift. Do not use
wall-clock time or assume gameplay font VRAM remains available during movies.
Validate original movie bytes, boundary frames, all captions, lyrics and runtime
playback before calling the conversion complete. No emulator desktop controls
were used, in accordance with pow's earlier instruction.
