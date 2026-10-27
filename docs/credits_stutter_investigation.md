# Ending credit stutter investigation — 2026-10-27

Status: offline investigation completed; the reported playback stutter is not
reproduced or fixed. No game build, movie payload, emulator setting or release
was changed. The user previously requested continuing without desktop control;
no emulator was launched or controlled. The user is unsure whether audio also
stutters.

## Supplied state

`incoming/ForPOWversion.p2s` is 17,788,011 bytes, SHA-256
`70539c007fb60d025bdd096ad68f4a574ceefeb965996092c92f6a9960455049`.
It was copied to ignored `work/source/credits-stutter/reported.p2s` and selected
entries were extracted with CRC checks. Its emulator version is PCSX2 2.9.146;
do not parse its internal structures using the earlier 2.8.2 state offsets.

The screenshot shows the scene before the credits. A 512-byte buffered pack at
EE 0xad9080 matches MOVIE002 at file offset 10,551,296; its pack clock is 11.0983
seconds. This establishes the ending movie, but the state is not a frame-time
capture of the stutter. This early portion is identical in the original and
translated movies, so that match does not establish the movie patch version.

Saved executable words retain the original linear HUD upload calls and the two
conditional refresh gates, with the shared font base 0x2600. The operator buffer
is still 50 glyphs. This is consistent with the older shared-font code; the
exact patch version is not established. The 0.1.31 unconditional font-refresh
change is absent and cannot explain stuttering in this supplied state.

## Full-movie checks

`tools/verify_movie_timing.py` extracts elementary streams directly from the two
PSS files, checks picture order and packet timestamps, and independently decodes
frame timing with ffprobe. The report is
`work/ui/credits-stutter/timing-audit.json`.

- Original and translated ending both contain 14,342 pictures in 797 GOPs.
- Both decode to all 14,342 frames; every consecutive presentation timestamp
  advances exactly 3,003 ticks at 90 kHz: 30000/1001 fps.
- Both have complete display indices, the same constant PTS/DTS bases, no
  repeat-frame flags and progressive frame pictures.
- All nonvideo bytes, including the audio and pack clocks, have identical
  SHA-256 hashes. This establishes unchanged audio data, not smooth runtime
  audio delivery.
- The credit renderer uses a continuous 1.17105-pixel-per-frame scroll with
  subpixel blending. No integer-frame hold is introduced by that calculation.

These checks rule out missing encoded frames, timestamp cadence gaps and
repeat-frame flags in the checked movie. They do not measure emulator speed,
display presentation, PS2 decoder workload or buffer occupancy.

## Packet-scheduling concern

The translated file has two B-picture starts after their calculated decode
clock, unlike the original:

| Display frame | Movie time | Start after decode clock |
| --- | --- | --- |
| 4919 | 164.130633 s | 23.656 ms |
| 4922 | 164.230733 s | 21.367 ms |

Both are in the GOP starting at display index 4912, during the staff roll.
The existing packer fits each re-encoded GOP into the original GOP's byte
budget, but does not constrain individual pictures against the pack clock.
Its overall-size check therefore does not rule out this scheduling risk.

SCR is a stream clock, not a measurement of actual disc arrival or emulator
presentation time. The game buffers movie data, so these two cases are not
proof of a visible hitch. They also do not explain repeated stuttering across
the entire staff roll. End-of-picture lateness must not be inferred using the
next picture's start: this stream contains substantial zero stuffing.

A 20-second reference export covering movie time 155–175 seconds is available
at `work/output/credits-stutter-reference-155s.mp4`, with the existing soundtrack
and native frame cadence. This MP4 is a comparison aid, not a PS2 patch or a
test of the console decoder.

## Remaining verification

The useful next evidence is emulator frame-time/speed data during the credit
roll, including whether audio breaks up, and comparison with the original PSS
under the same emulator conditions. The saved state begins before translated
text, making it a suitable replay starting point when playback testing is
available. Do not assume local PCSX2 settings describe the machine which
created this externally supplied state.

If a hitch repeatedly coincides with 164.13–164.23 seconds, test a local movie
variant that changes only GOP 4912's picture placement/encoding while retaining
all text, lyrics, audio and packet layout. No such variant is claimed here.
The ending movie is unchanged by local builds 0.1.30–0.1.32; those builds are
not credit-stutter fixes.

Reproduce the offline audit:

```text
py -3.11 tools/verify_movie_timing.py work/source/movies/MOVIE002.PSS work/output/movies/MOVIE002.PSS --out work/ui/credits-stutter/timing-audit.json
```
