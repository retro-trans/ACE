# Another Century’s Episode (Japan): translation text count

**Planning estimate: approximately 4,200 Japanese text entries.**

| Measure | Count |
| --- | ---: |
| Unique Japanese text entries, after removing formatting commands | **4,186** |
| Japanese text occurrences, including repeated copies | 10,347 |
| All nonempty table entries, including English and symbols | 11,247 |
| Unique nonempty strings, all languages, after removing formatting commands | 4,246 |
| Validated message tables | 564 |
| Compressed files decoded and checked | 157 |

## Breakdown of unique Japanese entries

| Category | Unique entries |
| --- | ---: |
| Mission dialogue, objectives and unit labels | 2,686 |
| Menus, briefings, descriptions and interface messages | 1,513 |
| Subtract entries present in both categories | −13 |
| **Total** | **4,186** |

The unique Japanese entries contain **85,792 characters excluding whitespace and formatting commands**. This includes punctuation and any Latin characters within Japanese entries; it is not a word count.

## What was counted

The local ISO’s DATA.BIN archive contains 3,026 indexed resources. The audit inspected these resources and decompressed all 157 CSC files. It parsed FMG message groups, message IDs and string pointers, then decoded their Shift-JIS/CP932 text. Empty pointers, unreferenced trailing text and standalone developer name-list files were not counted. Identical Japanese strings were deduplicated after removing inline display commands and outer whitespace. Internal spaces and line breaks were preserved, so some translation-equivalent variants still count separately.

One entry means one stored message or label, which can contain several displayed lines. The number of table occurrences is not a count of how often a player sees a message.

## Limits of the estimate

- This is a count of stored Japanese text, not a verified list of every message reachable during gameplay. It includes alternate resource versions and a few test/unused strings. Seven distinct strings were identified as obvious test content; removing just those would leave 4,179 entries in the tables.
- Japanese text drawn into textures, title graphics or movies is not included. Those need a separate visual audit. Audio-only dialogue is not counted.
- The executable also contains the Japanese game title, アナザーセンチュリーズエピソード, outside these tables. It is one additional text candidate; other inspected executable Japanese strings primarily describe internal resources or window types and require runtime review.
- The 60 non-Japanese unique strings include English labels, names, numbers, punctuation and formatting samples. Some English labels may also require translation depending on the target language.

## Saved evidence

- [Unique Japanese text](unique_japanese_text.txt)
- [Unique entries with all source locations and original control codes](unique_japanese_entries.json)
- [Parsed message tables](fmg_tables.json)
- [Archive inventory](inventory.json)
- [Compressed-file audit](compressed_audit.json)

The FMG structure was cross-checked against the [OpenCombas SoulsFormats implementation](https://github.com/OpenCombas/SoulsFormats/blob/main/Formats/FMG.cs). All counts above come from the local game files. CSC decoding was verified against matching uncompressed archive resources and exact declared output lengths. The original ISO and ZIP were not modified.
