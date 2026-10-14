# Brief for movie subtitle translators (MOVIE1 story cutscenes)

The 22 story cutscenes (`/MOVIE1/MOVIENNN.PSS`, specs named `M1_MOVIENNN`) have Japanese burned into the video:
subtitles in the dark bar under the picture, and title cards (date, place, character name) on black screens.
`tools/subtitle_scan.py` and `tools/subtitle_spec.py cards` have already found every card. Project root:
`E:\Projects\ACE`.

## Your input

* `work/translation/en/movies/subs/<movie>.json`: one entry per card: `id`, `frames`, `kind` (`subtitle` or
  `title`), `box`, `lines` (one band per Japanese line), and empty `ja` / `en`.
* `work/ui/movies/<movie>_cards.png`: every card cropped at 2x, labelled `#id fA-B kind`. Read the Japanese there.
  Zoom with PIL (crops into the scratchpad only) where a glyph is unclear.

## What to fill in

* `ja`: the Japanese exactly as shown, one line per line, joined with `\n` (keep the game's punctuation: `、。―…`,
  fullwidth or halfwidth as shown). This is for checking, it is not displayed.
* `en`: the English. Use `\n` to place the line break; keep the same number of lines as the Japanese (2 for almost
  every subtitle). Each line must fit about 60 characters (the tool condenses anything wider, so aim shorter).
  Subtitles that continue a sentence across cards should read as one sentence (end the first with a dash or
  nothing, start the next in lower case where natural).
* Title cards: `< Unified Earth Calendar 044, July`, `— Six months before the Refugee Ship Incident — >`; character
  cards: `— Ra Cailum Operations Staff Officer` / `Lucrezia Noin —` (follow these patterns).
* A detection that is not Japanese text (picture detail, English in the video, timecode): set `"skip": true`.
* Do not change `frames`, `box`, `lines` or `id`.

## Wording

Natural, concise English in the voice of the narrator or speaker (mostly Noin's log, first person). Use the
glossary (`work/glossary/glossary.json`, akurasu spellings: Ra Cailum, Londo Bell, UCE, Jaburo, Neo Zeon, ...)
and the established game terms in `docs/dialogue_translator_brief.md`. 統一地球暦 = Unified Earth Calendar.

## Check

Run `cd /e/Projects/ACE/tools && python subtitle_spec.py spec <movie>` and then
`python movie_text.py preview <movie> <frame> ...` for a few cards (a frame in the middle of each card's range);
view `work/ui/movies/<movie>_<frame>.png` (left original, right English). The Japanese must be gone and the English
legible and not squeezed.

## Report

Per movie: number of cards translated / skipped, anything unclear (card id and why). Edit only your movies' cards
files (and the generated specs).
