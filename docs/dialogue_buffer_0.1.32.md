# Operator dialogue drawing-buffer overflow

## Evidence from pow's saved hang

On 2026-10-26 pow confirmed the selection screen for campaign 39, Southern
Arabian Peninsula: Mop Up Remnants, and reported that the latest local build
hung as control passed to the player. A read-only copy of the PCSX2 slot-1
state was inspected without operating the desktop or emulator.

The state contains the 0.1.31 executable patches and internal-044 voice/model
resources. Its current operator message is row 69:

> Your unit is closest. Please protect the allied ship.

This is 53 ASCII characters. The saved message object at EE 0x172f810 holds
the same length in its typed counter. The operator widget at 0x1707fd0 points
to its drawing buffer at 0x1751900 and its private data at 0x1751880.

| Property | Saved value |
| --- | ---: |
| Drawing-buffer allocation | 5,776 bytes |
| Drawing packet emitted | 6,112 bytes |
| Overrun | 336 bytes |
| Current EE PC | 0x13d5f0, waiting for VIF1 DMA |
| VIF1 CHCR | 0x10000155 (transfer still active) |
| GIF STAT | 0x0e80 |

The GIF stream contains the setup and all 53 glyph packets. At packet offset
0x17d0, the expected terminating tag has been replaced by neighbouring object
data. Decoding that data as a GIF tag requests 0x425000 bytes. VIF1 is waiting
on a DIRECTHL operation while the GIF path has not finished. Earlier log entries
record invalid memory reads in gameplay code as well.

## Code and correction

EE 0x2018dc supplies `50` to the sizing function at 0x1c9220. Its nonzero-count
calculation is `(7 * glyph_count + 11) * 16`: seven qwords per glyph and eleven
qwords of setup/termination. The widget stores the size at private-data +0x28
and obtains that many bytes from the existing heap allocator. Its update path
at 0x201a10 calls the renderer at 0x1c8a10 with the actual typed length, which
is not capped to the allocation's 50 glyphs.

0.1.32 changes the allocation immediate from 50 to 128, reserving 14,512 bytes
through the original allocator and recording the larger size normally. It costs
8,736 extra bytes per widget. No heap address, packet format, text, event flag,
mission logic, font texture or upload path is changed.

The previous 54-byte operator limit came from incomplete playtests and did not
protect this drawing buffer. Japanese text uses fewer glyphs per encoded byte,
so byte-length comparisons with the Japanese original were misleading. Existing
translation limits remain in place; they are below the new capacity. The separate
132-byte typewriter buffer and its stricter translation limits are unchanged.

## Verification and limits

`tools/verify_dialogue_buffer.py` verifies the actual sizing instructions, new
allocation instruction, all translated message byte budgets, and (when given
the local extracted state) the saved widget's allocation/packet discrepancy and
malformed GIF tag. `work/ui/dialogue-buffer-0.1.32/` holds numeric evidence.
All extracted RAM, original code, state archive and its screenshot remain under
ignored `work/source/hang-0.1.31/`.

The layout audit passes all 3,493 rows. Of those, 3,235 contain translated text;
the longest stored visible message is 93 bytes. There are 271 operator rows
over the old 50-byte threshold, including 025 rows 23, 31, 50, 57, 78 and
044 rows 18, 50, 61, 62, 63, 67, 69. This inventory is conservative (encoded
byte counts); the saved row is ASCII, so its 53-glyph overrun is exact.

Built ISO: `work/output/ACE-EN-0.1.32.iso` (3,357,147,136 bytes), SHA-256
`72d807e7b9e8f02f54b2ff3f491ed0fdb60c4cbf15dabdb81a0195217b248f73`.

Finished-image checks passed: `iso-verification.json` checks the allocation
in the built executable and all message budgets. `scope-verification.json`
compares every game resource and every other disc file against 0.1.31,
including full hashes of the movie files. Only the allocation instruction and
three title-stamp copies differ. The build's resource/movie readbacks and
ISO/UDF consistency checks also pass. These checks retain all 4x fonts and
lyrics but do not verify gameplay or mission completion.

The internal state register layout was checked against PCSX2's version-matched
[R5900.h](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/R5900.h) and
[SaveState.cpp](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/SaveState.cpp).
This is analysis of saved memory, not an emulator replay or a completed mission.
The state proves an overflow in the reported hang; it does not prove the
0.1.31 font-refresh change caused it. The allocation was also 50 glyphs in
earlier builds.

Retest by booting the new ISO and loading the normal memory-card save, then
starting the mission again. Loading the hanging emulator state would restore
the old executable/allocation and already-corrupted heap.

## Earlier post-retreat report

The earlier Jeril line from the 0.1.30 screenshot is present in internal 025,
whereas the latest menu screenshot and hang state identify 044. That discrepancy
remains unresolved. Both missions contain operator messages beyond the original
50-glyph capacity, so this bug is relevant to both investigations. Completion
after Jeril's retreat still needs testing; no mission-event modification or
claim of verified completion is justified by the available state.
