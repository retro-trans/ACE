# Brief for dialogue translators

Game: Another Century's Episode (PS2, 2005), a mecha action crossover of Gundam Wing, Zeta/ZZ/Char's
Counterattack Gundam, Nadesico: The Prince of Darkness, Dunbine, Layzner, Brain Powerd, Dragonar, Heavy Metal
L-Gaim and originals. You translate **in-mission radio dialogue and objective labels** into English.
Project root: `E:\Projects\ACE`.

## Files

* Your files: `work/translation/en/dialogue/mNNN.json`. Edit only the files you were assigned. Load, modify and
  save with a small Python script (UTF-8, `ensure_ascii=False`, `indent=1`), kept outside the project.
* Format: `{mission, context: {briefing_ja, flow_chart}, units, rows: [{id, ja, en, notes}]}`. Fill `en` and a
  `speaker` field for every row, and use `notes` for non-obvious decisions. Do not change `ja`. Leave `units`
  alone.
* Context: `briefing_ja` is the mission's briefing table (1 name, 2-4 objectives, 100+ briefing, 200+
  debriefing, 300 failure line). `flow_chart` is the akurasu.net walkthrough entry. Rows 1-9 are usually
  objective labels (short HUD text); rows 10+ are radio dialogue in order.
* Story so far: `work/glossary/mission_order.json` lists missions in story order. You may READ the already
  translated earlier missions (`m*.json` with `en` filled) to keep character voices, terms and running jokes
  consistent. Never edit them.

## Speakers

The game does not store who speaks. Infer the speaker from content, register, address terms and the rows on
either side (read both before deciding). Record your inference in `speaker`, or `?` when the scene does not
settle it. Never assume gender for an unknown speaker; keep the wording neutral. Rows 50-79 (or 40-49) are often
ten **selectable-operator** variants of the same line (slots repeat every 10 rows): keep each slot's voice as
earlier missions established it. Slot 7 is a machine voice in katakana: ALL CAPS, clipped.

## Text rules

* Write only the visible text. The Japanese rows look like `<op()><sp(20)>…<ab(1000)>`; the tool re-attaches
  the `<...>` tokens. Your `en` must contain no tokens.
* Timing-only rows (tokens with no visible text): leave `en` empty.
* One row in, one row out. Never merge or split rows. A sentence cut across two rows is cut at the matching
  point in English. `<ab(0)>` means the row continues immediately into the next one.
* Keep button symbols (○ □ △ × ① ② ③ ④ ⑤) where the Japanese has them; write R1, L2 and the like in ASCII.
  Drop `#c[FF0000]` / `#c` pairs that only wrap a line break.
* Printable ASCII only, plus those symbols and ν. No curly quotes, no em dashes ("..." for trailing off),
  no accented letters, no "%".

## Limits (checked by the tool)

At most 2 lines, each 400 units or less (about 60-65 characters), and 128 bytes or less per row. The tool wraps
automatically into a balanced two-line split; "\n" forces a break. Write the full meaning first; compress only if
the check complains. Never drop the end of a sentence. If a row cannot fit, leave your best version and flag it.

## Translation rules

Read `BASE_RULES.md` fully and follow it, especially:

* Restore subjects and verbs that Japanese grammar drops (for example, "I'm counting on you"), and check the
  direction of requests.
* Use lively spoken English, with a military radio register where it fits.
* Keep insults and threats at full strength, and never assume gender.
* Report every row where you kept an ambiguity.

Names and terms come from `work/glossary/glossary.json` (including `ranks` and `dialogue_conventions`),
`decisions.json` and `akurasu_terms.json`, plus the raw akurasu pages in `work/glossary/akurasu/`. akurasu.net is
the main source: research missing names at https://akurasu.net/wiki/ and report them with URLs. Unit names use
the series-standard English.

## Check, then report

    cd /e/Projects/ACE && python tools/dialogue_layout.py check NNN [NNN ...]

Fix every PROBLEM. Optional proof: `python tools/dialogue_layout.py preview NNN` writes `work/ui/dialogue/`.

Final report (concise, as your last message): rows examined versus rows in your files; names researched (with
URLs); uncertain calls (speakers, referents, kept omissions with row ids); and the last line of the check output.
Do not paste the translations.

## Operator window: one line only

Rows shown in the operator window (a row with `<op()>` and the rows after it until one ending in `<ed()>`) must
fit on **one line of at most 400 units**. The Japanese never breaks a line there, and a two-line message in that
window hangs the game (found in play, mission 1). Shorten the wording; keep the meaning, the speaker's voice and the
established terms; no explicit `\n`. `python tools/dialogue_layout.py check mNNN` reports the width of every
offending line. When the same Japanese line occurs in several missions, give it the same English everywhere.

Operator-window rows are also limited to **54 visible bytes** (one byte per English character, two for fullwidth
symbols such as △ □ ○ ×). A 57-byte row crashed the game in play (mission 1 row 69); the Japanese never exceeds 52.
The check reports "N visible bytes (max 54 in the op window)".

Operator rows spoken by a `<cs(n)>` speaker (the enemy and guest speakers whose rows start with `<cs(1)>` etc.) are
held to **46 visible bytes**: the speaker colour shares the message buffer. A 53-byte row stalled mission 3's script
(the enemy could not retreat). The check reports "N visible bytes (max 46 ...)".
