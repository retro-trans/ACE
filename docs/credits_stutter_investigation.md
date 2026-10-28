# Ending credit stutter investigation — 2026-10-27

Status (2026-10-28): repeated frame-group stalls reproduced in an isolated
PCSX2 replay and substantially reduced by lossless movie repacking. The user
explicitly authorized isolated emulator replay windows after initially asking
for work without desktop control. Normal emulator settings, memory cards and
public releases remain unchanged. The original offline findings follow below.

## Runtime follow-up and padding fix

After the user reported that the MP4 exports played correctly, compared the
original game, 0.1.29 executable and saved RAM. Movie-player ranges
`0x1ef910..0x1f3000` and `0x1ffe90..0x200b80` are identical in all three.
The saved ring is valid: capacity 2, producer 1, queued 1. A snapshot alone
does not establish playback cadence.

Ran three isolated PCSX2 2.8.2 sessions, using the same supplied state, 0.1.29
executable and 4x D3D12 renderer. No keyboard/mouse input was sent. Test-only
data directories, disabled memory cards and muted output kept the regular
installation unchanged. The third ISO is a diagnostic copy of 0.1.29 with
only MOVIE002 repacked; its executable/title intentionally stay 0.1.29 for
state compatibility. It is not the normal 0.1.34 build.

Read-only PINE sampling tracked the MPEG decoder counter and output queue;
PresentMon 2.6.0 independently recorded host presents. The baseline host
present interval was mostly regular (median 16.68 ms, p99 17.35 ms), while
the movie decoder repeatedly paused at GOP boundaries. Of 129 decoder gaps
over 60 ms, 127 were at GOP starts. For example, counter 1961 followed
137,623 zero bytes and paused 104.44 ms. The translated ES contains roughly
90.9 MB of long zero runs, compared with 6.8 MB in the original movie.

Matched decoder-counter range 1500–4500:

| Test | Average decoded fps | Consecutive-counter gaps >60 ms |
| --- | ---: | ---: |
| Existing 0.1.29, VSync off | 29.13 | 56 |
| VSync + host refresh/timing synchronization | 28.53 | 84 |
| Repacked ending, original VSync-off settings | 29.96 | 2 |

The repacked run's two remaining consecutive-counter gaps in that range were
about 61 ms. Sampling includes host scheduling noise; long polling gaps with
counter jumps are not counted as single-frame stalls. PresentMon's display
tracking had many discarded/occluded presents, so it does not certify visible
display cadence. This identifies excessive video stuffing as a repeatable
cause in this replay, not every possible source of stutter.

`tools/movie_pacing.py` retains small alignment runs but replaces long video
stuffing with MPEG-PS padding streams (0xBE). It splits only original video
PES ranges; picture headers/timestamps, encoded picture data, original pack
clocks, all original nonvideo ranges and total PSS length remain intact.
90,879,883 video-stuffing bytes were moved out of the ending video stream.
FFmpeg frame-MD5 comparisons prove every one of its 14,342 decoded pictures
and timestamps is identical. The same full-frame check covers the repacked
news and opening movies. This keeps translations and karaoke pixel-exact.

Evidence: `work/ui/credits-stutter/replay-comparison.json`,
`{baseline,synchronized,repacked}.json`, `padding-correlation.json`,
`repack-video-verification.json` and `MOVIE00N-pacing.json`. Raw queue and
PresentMon CSVs are retained in ignored `work/source/credits-stutter/traces/`.
`tools/trace_movie_playback.py` only sends PINE identification and RAM-read
commands; it never changes memory or sends input. Its protocol was checked
against the official PCSX2 2.8.2 source and a saved-RAM socket fixture.

The state was created with PCSX2 2.9.146 and a Japanese BIOS, whereas these
controlled replays used installed 2.8.2 and the available US BIOS. All three
tests used the same combination; fresh-boot confirmation on the user's usual
configuration remains useful. No emulator-global timing settings were changed.

Sources for emulator settings and measurements:
[PCSX2 2.8.2 timing settings](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-qt/Settings/EmulationSettingsWidget.cpp),
[PCSX2 target-speed logic](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/VMManager.cpp),
[PresentMon](https://github.com/GameTechDev/PresentMon).

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

### Full 0.1.29 MP4 exports (2026-10-27)

The user subsequently confirmed noticing the stutter in 0.1.29 during the song.
Extracted both song movies directly from `work/output/ACE-EN-0.1.29.iso`:

- `work/output/mp4/0.1.29/ACE-0.1.29-Ending-Credits.mp4`: 14,342 frames,
  478.544733 seconds of video, 116,570,676 bytes.
- `work/output/mp4/0.1.29/ACE-0.1.29-Opening-Garnet-Moon.mp4`: 5,410 frames,
  180.513667 seconds of video, 62,334,367 bytes.

Both retain 512x448 pixels, with 7:6 sample aspect ratio for 4:3 display,
30000/1001 fps, and exactly the source decoded frame counts. H.264 CRF 16
and stereo AAC 320 kbps; no interpolation, scaling or frame-rate conversion.
Existing translations, lyrics and karaoke are included. The complete extracted
48 kHz soundtrack is retained, including its approximately half-second tail
beyond the last video frame. Source and output hashes, audio sample counts and
stream metadata are in `work/output/mp4/0.1.29/export-report.json`.
The ending sample at 170 seconds was visually checked. These are PC playback
comparison files, not a game build or proof of smooth PS2 playback.

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
