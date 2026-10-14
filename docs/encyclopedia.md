# Terminology database (encyclopedia)

Menu entry: 専門用語を調べます ("look up technical terms"). Text table `f205.fmg`, present in
`MenuCampaign.csc`, `MenuFree.csc` and as a standalone resource; all three copies are identical and all are
replaced.

## Structure

* Ids 1-31: organizations and setting terms; 41-60: control tutorials; 61-97: playable units. Ids 32-40 and
  98-100 are empty slots and are kept.
* Description pages are `term * 100 + page`. 88 terms, 142 Japanese pages.
* **Pages are counted at run time.** EE `0x2760d0` looks up `f205` (resource 46405) and probes
  `term*100+1, +2, ...` with the FMG lookup at `0x1cff80` until one is missing. An English page that does not fit
  continues on extra ids, with no code change.
* The page text is passed to a printf-style setter (`0x210c30`, formats into a 1 KB stack buffer), so a literal
  `%` must be stored as `%%` (`encyclopedia_layout.stored`).
* The copy routine `0x212040` widens ASCII digits to 2-byte codes. The widget buffer is allocated from the layout
  descriptor (`desc+0xc`, 1-1024 bytes; 64 inline bytes otherwise).

## Limits used (measured from the stock data)

| Limit | Value | Evidence |
| --- | --- | --- |
| Line width | 440 units | widest Japanese line 442 (id 5001) |
| Lines per page | 8 | 67 Japanese pages use 8; one uses 9 |
| Bytes per page | 390 | largest Japanese page 391 bytes (id 2901), counted with digit widening |
| Title | 27 bytes, 230 units | largest Japanese title 27 bytes / 230 units |

The exact descriptor capacity of the body widget was not located. Staying within the largest Japanese page
guarantees the buffer is large enough.

## Control codes

`#c[FF0000]` ... `#c` occurs 135 times in f205 (and 20 times in mission text), and every occurrence wraps only a
line break: no visible glyph is ever coloured. Because English re-wraps every line, the pairs are not carried over.
If they turn out to matter in game, they can be restored around line breaks.

## Translation workflow

1. `python tools/encyclopedia_source.py` exports the Japanese to `work/source/encyclopedia_ja.json` (local only).
2. The working file is `work/translation/en/encyclopedia.json` (`title_en`, `pages[].en`, `notes`). Prose is
   written without line breaks; `\n` marks structure; leading spaces form a hanging indent.
3. `python tools/encyclopedia_layout.py check` wraps, paginates and checks limits;
   `... preview <term>` renders PNG proofs with the real atlas and metrics (`work/ui/encyclopedia/`).
4. `python tools/build.py <version> --write` builds the ISO.
5. `python tools/strip_jp.py` writes `encyclopedia.en.json` (the only translation file to commit).
