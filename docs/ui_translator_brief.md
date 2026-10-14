# Brief for UI translators

Game: Another Century's Episode (PS2, 2005). You translate the remaining menu and HUD text: weapon and unit
names, part labels, menu help lines, option descriptions, memory-card messages, pause dialogs, radio speaker
names and lock-on target labels. Project root: `E:\Projects\ACE`.

## Files

* Your files: `work/translation/en/ui/<group>.json`. Edit only the files you were assigned. Load, modify and
  save with a small Python script (UTF-8, `ensure_ascii=False`, `indent=1`), kept outside the project.
* Each file holds `{group, font, limits, where, rows: [{id, ja, en, notes}]}`. Fill `en` and use `notes` for
  non-obvious decisions. Do not change `ja`, `font`, `limits` or `where`.
* Variant files (`*_v2`, `*_v3`) are near-copies of the main group from other menu bundles. Rows with the same
  `ja` as the main group must get the same `en`.

## Rules

* Names: use akurasu.net first. For mech names, see `work/glossary/akurasu_terms.json`; for weapon names, the
  weapon tables in `work/glossary/akurasu/ACE_Mech_Database.wiki`. Then use `work/glossary/glossary.json` and
  `decisions.json`. Stay consistent with the already translated encyclopedia, dialogue and briefings
  (`work/translation/en/encyclopedia.json`, `dialogue/`, `briefing/`), which use the same terms.
* Menu help lines and descriptions: concise, imperative or descriptive UI English ("Start the mission",
  "Adjust your unit").
* Memory-card messages: standard PS2 wording ("MEMORY CARD (PS2)", "MEMORY CARD slot 1", "Do not remove the
  MEMORY CARD (PS2) or reset/switch off the console"). Keep every format code (`%1d`, `%d`, `%s`) exactly, in the
  same order. Use "\n" line breaks: these dialogs have fixed lines, so break the message into sensible lines yourself.
* Radio speaker names (`speakers`) and lock-on labels (`lockon`): very short, title case, mech or character
  names. Speaker names are short forms as shown on the radio window (for example "Bright", "Sally", "Ciela").
* ASCII only, no "%" except in format codes, no curly quotes or accented letters. The `f005` and `hud13` fonts have
  **only** printable ASCII.

## Limits (checked by the tool)

Each group's `limits` (lines, width in font units, bytes) were measured from the longest Japanese row; staying
within them guarantees the text fits the game's boxes and buffers. Abbreviate where needed ("MP" for Mass
Production, "Lt." and so on), but keep the meaning.

## Check, then report

    cd /e/Projects/ACE && python tools/ui_layout.py check <group> [<group> ...]

Fix every PROBLEM. Final report (concise, as your last message): rows examined versus rows in your files; names
researched (with URLs); uncertain calls; and the last line of the check output.
