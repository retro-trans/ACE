English fan translation of **Another Century's Episode** for PS2 (**Japan, SLPS-25394**), with restored story-movie subtitles, opening/ending lyrics and corrected menu panels.

### Apply

**Recommended:** Use [Retro Trans](https://github.com/retro-trans/retro-trans-tools). Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO, choose **English** and **0.1.26** (or **Latest**), and select a new output filename.

**Manual patching:** Use [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or xdelta3:

| Source image | Patch |
| --- | --- |
| Original Japanese SLPS-25394 ISO | `ACE-English-0.1.26.xdelta` |

```text
xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.26.xdelta "ACE English 0.1.26.iso"
```

Original image: **3,357,147,136 bytes**, SHA-256 `7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9`.

Release output: **3,357,147,136 bytes**, SHA-256 `95b7fafe2b4c5ddbfbd276f1322cb4cc08479891af0b714db3520b481472244c`.

This is a full patch from the original Japanese disc. When upgrading, apply it to your original ISO again; earlier English images are not patch inputs. Retro Trans handles supported DVD CHD extraction; manual patchers require the unpacked ISO.

`BUILD-MANIFEST.json` records the exact source, output and patch identities. `VALIDATION.json` records the full patch round trip, and `SHA256SUMS.txt` covers the downloads.

### What changed since 0.1.20

- **Story movies:** restores English title cards and subtitles in all 22 story cutscenes, including Gavlet Gablae's interviews.
- **Fonts:** upgrades speaker names and lock-on labels to the 4x font, preserving their on-screen size, spacing and the original HUD warning glyphs.
- **Title screen:** adds the patch version and `github.com / retro-trans` in the bottom-right corner.
- **Carrier information:** removes split labels and stretched gray bars across the value column. Uses concise Carrier and Squad labels.
- **Launch Setting:** removes the repeated fragment beside Resources and the stretched line after Repair Eff.; both headings retain their full wording.

Retains the mission 3 progression fix, corrected difficulty/controller menus, AREA OVER warning, English news/ending text and credits, and both songs' romaji karaoke and English lyrics. The ending lyrics use the larger overlay across the bottom of the credits. See the [changelog](https://github.com/retro-trans/ACE/blob/main/docs/CHANGELOG.md).

### Release status

**Further proofreading and a full playthrough are needed.** The mission 3 progression fix was confirmed in play. Earlier builds had confirmation for mission 1 (tutorial and aerial combat), mission 2's briefing, the title screen and the save screen. The latest panels, restored story movies, ending movie and other routes still need in-game review. The 4x HUD font's larger graphics-memory allocation still needs gameplay confirmation.

Automated checks passed for the final disc layout/payloads, text-table inventory and corrected texture copies. All 22 restored story movies decode to the expected frame counts; all 25 translated movies preserve their original audio/nonvideo data. Both songs' 52 lyric rows pass layout checks. The complete patch output is decoded and verified before publication. These checks do not certify every emulator, console or gameplay route.

Four credit readings remain provisional: **Mitsuo Hasegawa, Naoizumi Tazo, Rights In and Artprest**. Some fast-moving news shots were re-encoded at lower quality to fit the original movie space. See [movie notes](https://github.com/retro-trans/ACE/blob/main/docs/movies.md).

**Boot the patched ISO fresh and load a normal memory-card save.** Older save states can restore old text, fonts and layout data.

### What's included

English menus, help, names, objectives, briefings, mission dialogue, Terminology entries, UI textures, 22 story movies, news captions, ending epilogue and credits, and bilingual opening/ending lyrics with karaoke. Japanese audio is preserved. MOVIE005 stays original.

### How it was translated

This is a **machine translation**, produced with large language models and reviewed and edited using scene context and a researched glossary. Terminology primarily follows Akurasu, with documented exceptions. Human proofreading and playtesting are welcome.

### Acknowledgements

- **Project lead and playtesting:** pow
- Tools and release structure build on [ACE-3](https://github.com/retro-trans/ACE-3) and [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools).

### Source code

English translation exports, glossaries, layout metadata and tools are in the [project repository](https://github.com/retro-trans/ACE). GitHub's source archives contain the repository at the release tag. Use the `.xdelta` asset to patch the game; development rebuilds require local source exports.

### Contribute

Report bugs and translation issues through [GitHub Issues](https://github.com/retro-trans/ACE/issues), including the patch version, mission and reproduction steps.

No complete game images are included. Apply the patch to your own disc image.
