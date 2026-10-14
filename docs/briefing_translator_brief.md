# Brief for briefing and debriefing translators

Game: Another Century's Episode (PS2, 2005). You translate each mission's **menu table**: the mission name,
objective labels, pre-mission briefing, post-mission debriefing and the failure line. These are story text
spoken by the commanding officers. Project root: `E:\Projects\ACE`.

## Files

* Your files: `work/translation/en/briefing/fNNN.json`. Edit only the files you were assigned. Load, modify and
  save with a small Python script (UTF-8, `ensure_ascii=False`, `indent=1`), kept outside the project.
* Rows `{id, ja, en, notes}`. Fill `en`, add a `speaker` field (your inference, or `?`), and use `notes` for
  non-obvious decisions. Do not change `ja`.
* Row meaning:
  * id 1: mission name. Use the akurasu flow-chart name (`work/glossary/akurasu/ACE_Flow_Chart.wiki` and
    `mission_order.json`, where `flow_chart` holds "Mission N - Place: Name"); give only the part after the
    colon, e.g. "Combat Training".
  * ids 2-4: HUD labels for the victory condition, defeat condition and secret objective. They must match the
    in-mission objective labels already translated in `work/translation/en/dialogue/mNNN.json` (rows 1-4) where
    the Japanese is the same.
  * ids 100+: the briefing, in order. ids 200+: the debriefing, in order. id 300: the line shown when the
    mission is failed.
* The same mission's in-mission dialogue is already translated in `work/translation/en/dialogue/mNNN.json` (same
  NNN). Read it, and the neighbouring missions in story order (`work/glossary/mission_order.json`), for
  speakers, voice and terms. Never edit those files.

## Tokens inside the text (important)

The Japanese contains control tokens in the middle of sentences: `<cs(3)>text<ce()>` colours a phrase,
`<pic(1)>` shows a picture, `<mk(25,-25,1,1)>` and `<ar(0,1,1,50)>` draw map markers and arrows, and `<pt(...)>`.

* Your `en` must contain **exactly the same tokens in the same order** (copy them verbatim).
* Put `<cs(n)>` and `<ce()>` around the English words that correspond to the coloured Japanese phrase.
* Put `<pic>`, `<mk>`, `<ar>` and `<pt>` at the point in the English sentence that corresponds to their
  position in the Japanese (they are timed to the text). If the word order changes, place them before the
  corresponding phrase.
* Line breaks: the tool wraps automatically into at most two balanced lines. Use "\n" only to force a break,
  which you will rarely need. A row is one text box: one row in, one row out.

## Limits (checked by the tool)

* Name: 1 line, 200 units, 27 bytes.
* Objectives: 2 lines, 200 units (a narrow box: about 30 characters per line), 60 bytes.
* Briefing, debriefing and failure: 2 lines, 440 units (about 55 characters per line), 120 bytes.

Write the full meaning first; compress only when the check complains, and never drop the end of a sentence.
Use printable ASCII only (plus the game's button symbols if the Japanese has them). No "%", curly quotes, em
dashes or accented letters.

## Translation rules

Follow `BASE_RULES.md` (restore dropped subjects, no softening, no gender guessing, report ambiguities). Use the
glossary (`work/glossary/glossary.json`, `decisions.json`, `akurasu_terms.json`). Use the military briefing
register for briefings and a natural spoken register for debriefing banter.

## Check, then report

    cd /e/Projects/ACE && python tools/briefing_layout.py check NNN [NNN ...]

Fix every PROBLEM. Final report (concise, as your last message): rows examined versus rows in your files; names
researched (with URLs); uncertain calls; and the last line of the check output. Do not paste the translations.

## Byte limits = the Japanese maxima (2026-10-14)

Two in-mission text buffers turned out to be sized for the Japanese (a longer English line crashed the game), and
the briefing buffer is not located, so every briefing row is now held to the Japanese maximum: mission name 27
bytes, objective labels 39, briefing / debriefing / failure text 89 visible bytes (digits count double; tokens do
not count). `python tools/briefing_layout.py check NNN` reports "N bytes (max M)". Shorten the wording, keep the
token sequence and the meaning; when a sentence spans two rows, keep it reading as one.
