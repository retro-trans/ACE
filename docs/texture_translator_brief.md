# Brief for texture (baked-in lettering) translators

Some menu and window textures of Another Century's Episode have Japanese labels painted into the image (tabs,
headers, stat names, buttons). `tools/texture_text.py` erases a label and draws English in its place.
Project root: `E:\Projects\ACE`.

## Workflow per texture

1. Run `cd /e/Projects/ACE/tools && python texture_text.py detect <name>`, then view
   `work/ui/texture_text/<name with . replaced by _>_detect.png`. It shows the texture at 3x with numbered red
   boxes; `..._boxes.json` holds the boxes in texture pixels `[x0, y0, x1, y1]` (x1/y1 exclusive).
2. Write `work/translation/en/textures/<name with . replaced by _>.json`:

       {"name": "t0403.tm2", "labels": [
         {"box": [21, 4, 94, 24], "ja": "戦艦情報", "en": "Carrier Info", "align": "left", "grow": [0, 20]},
         {"box": [x0, y0, x1, y1], "ja": "...", "en": "...", "vertical": true}
       ]}

   * One label per Japanese word or phrase. Use the detected boxes where they are right. Merge, split or adjust
     them by hand where detection is off (it may split a word, join two words, or miss thin or coloured
     lettering). The box must cover the whole Japanese lettering **including its 1-2 px dark shadow**, and
     nothing else (no button edges or lines).
   * `grow: [left, right]` lets the English use free background next to the box (plain button fill only).
     The erase uses the pixels just outside the grown box, so never grow over edges, icons or other labels.
   * `align`: left, center or right, matching how the Japanese sits on its button.
   * Vertical Japanese labels: `"vertical": true`; the English is drawn rotated, reading top to bottom, and
     `grow` then extends up and down.
   * Leave out any box that is already English, a symbol or graphics; a label is changed only when it has `en`.
3. Run `python texture_text.py render <name>` and **view** `..._render.png` (before | after). Check that no
   Japanese remains, nothing outside the labels changed, the English is legible and not squeezed below about
   70 percent, the text sits centred on its button, and line art is intact. Fix the boxes and render again
   until it is clean.

## Wording

Short UI English in Title Case, matching the game's menus (already translated). Established terms:

* Carrier (戦艦), Hangar, Repair Res. (倉庫, 修理資材), Repair Eff. (修理効率), Ace Points (エースポイント).
* Armor, Speed, Vernier, Output, Mobility, Turning (旋回性能), Wpn Power (兵器出力), Wpn Reload (兵器性能).
* Defense, Energy, Movement, Mood (気分).
* Main, Melee (近接), Sub, Attach 1/2, Special, Ability 1/2, Shield.
* Rookie, Pilot, Ace (difficulty).
* Semi-Auto, Manual, lock-on, Dash, Ascend (上昇), Descend (下降), Camera / Front / Distance / Damage Priority.
* Mission name, Victory Cond. (達成条件), Defeat Cond. (敗北条件), Secret (シークレット).
* Friendly 01-03, Sortie (出撃), Mission Results, Clear Time, Kills (撃墜数), Damage Rate (破損率).

Abbreviate where the space forces it (Cond., Pts, Eff., Res.), but keep each label clear.

## Report

Final message (concise): textures done, labels per texture, anything you could not translate cleanly (and why),
and confirmation that you viewed every render. Edit only your own spec files.
