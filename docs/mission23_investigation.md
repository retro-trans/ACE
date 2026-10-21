# Mission 23 does not finish (2026-10-22)

The reported player defeated all enemies but the mission did not end on the latest
public build, **0.1.26**. The supplied file is `incoming/ace_mission23.ps2`.
The cause is **not confirmed**. No gameplay reproduction or fix is claimed.

Campaign mission 23, Investigate Enemy Base, maps to **internal mission 025**.
Internal mission 023 is Recapture Jaburo (campaign mission 19); do not diagnose the
wrong dialogue table. The local glossary's flow-chart context identifies the mapping.

## Findings

- The submitted 8,650,752-byte image has the PS2 memory-card format header. Its ACE
  directory and all four file allocation chains were readable, including the
  46,208-byte `BISLPS-25394-ACE00` save. This is not a save state of the stalled event.
  The game's save checksum and mission progression fields have not been decoded.
- Original card SHA-256:
  `d0d2e5de3533d5b32905dcd75775af02be8358d4d84df33101d9aa349abf8082`.
  Inspection never writes the submitted file. Private extractions and a test copy
  are under ignored `work/source/mission23-test/`.
- All 70 mission 025 translation rows pass the existing layout limits. The actual
  released strings match the translation sources; control tokens and row IDs match
  the original. Passing these checks does not rule out an undiscovered runtime limit.
- Mission 025's map resources, enemy bundle and all 550 AI logic resources match the
  original disc (553 resources checked). No mission completion trigger has been edited.
- The previous mission 3 overflow is a hypothesis to investigate, not an established
  explanation for this report. Do not shorten lines arbitrarily and call it fixed.
- The user requested continuing **without desktop control**. No emulator gameplay
  test was performed. A briefly launched background test process was stopped; the
  shared emulator configuration and existing memory cards were not changed.

## Diagnostic build 0.1.27

`tools/mission_diagnostic.py` creates a local diagnostic copy of the verified public
0.1.26 ISO. It restores only internal mission 025's dialogue rows (ids >= 10) to the
original Japanese, and updates the three title-version texture copies to 0.1.27.
English objectives and lock-on names stay intact. No translation source is modified.
All other ISO bytes, including movies, lyrics, fonts, scripts and filesystem records,
are checked against 0.1.26. This is a diagnostic build, **not a release or confirmed fix**.

```text
python tools/mission_diagnostic.py --baseline 0.1.26 --version 0.1.27 --mission 025
python tools/mission_diagnostic.py --baseline 0.1.26 --version 0.1.27 --mission 025 --write
```

Output: `work/output/ACE-EN-0.1.27-dialogue-diagnostic.iso`. Its JSON report records
the output identity and verification results. The tool refuses to overwrite it.
Completed: **3,357,147,136 bytes**, SHA-256
`7ba2521692255fc8aa7b518bf5e480340413e405d8e680f0ebdeff245c50205a`.
The full byte comparison and four resource readbacks passed; movies and lyrics are
identical to public 0.1.26. The submitted card's hash remained unchanged.
Evidence is in `work/ui/mission23/`.

## Next test

Boot the diagnostic ISO fresh, load a normal memory-card save from before mission 23,
and replay it. Do not load a save state created on 0.1.26, which could restore the old
dialogue and already-stalled state.

- If the same route finishes, bisect mission 025's translated rows to locate the
  offending line or combination, then fix that case and add a meaningful check.
- If it still stalls, record the last spoken line and whether the Leprechaun and
  enemy facility events occurred. Compare the original Japanese disc from the same
  normal save before assigning the cause to translation, font allocation, or game logic.

No new GitHub release is authorized by this bug report. Public Latest remains 0.1.26.
