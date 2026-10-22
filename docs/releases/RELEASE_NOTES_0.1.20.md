English fan translation of **Another Century's Episode** for PS2 (**Japan, SLPS-25394**), with the mission 3 progression fix, corrected menus, and restored HUD warnings.

### Apply

**Recommended:** Use [Retro Trans](https://github.com/retro-trans/retro-trans-tools). Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO, choose **English** and **0.1.20** (or **Latest**), and select a new output filename.

**Manual patching:** Use [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or xdelta3:

| Source image | Patch |
| --- | --- |
| Original Japanese SLPS-25394 ISO | `ACE-English-0.1.20.xdelta` |

```text
xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.20.xdelta "ACE English 0.1.20.iso"
```

Original image: **3,357,147,136 bytes**, SHA-256 `7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9`.

Release output: **3,357,147,136 bytes**, SHA-256 `45148f8c96a06d8cc5129de216dcf0f36830cb3f82f4f4f1c82652af79168082`.

This is a full patch from the original Japanese disc. To upgrade from 0.1.17 or a local test build, apply this patch to your original ISO again. Earlier English images are not inputs for this patch. Retro Trans handles supported DVD CHD extraction; manual patchers require the unpacked ISO.

`BUILD-MANIFEST.json` records exact source, output and patch identities. `VALIDATION.json` records the complete patch round trip, and `SHA256SUMS.txt` covers the downloads.

### What changed since 0.1.17

- **Mission 3 progression:** fixed the final Muzura remaining at zero armour instead of withdrawing. The corrected mission was confirmed in play. Operator messages with speaker-color codes now use a 46-byte visible-text limit; 79 rows across 36 missions were adjusted to prevent the same overflow.
- **Difficulty:** centered Rookie, Pilot and Ace vertically in normal and highlighted states.
- **Controller settings:** restored full right-side labels in Manual and Semi-Auto diagrams.
- **HUD:** restored the original AREA OVER warning and related CAUTION, ON AIR, MISSILE and ERROR labels by retaining their font characters.
- **Movies:** retains the opening and ending romaji karaoke and English lyrics, including the larger ending overlay across the bottom of the credits. English news captions, the ending epilogue, staff credits and producer/publisher cards are included.

See the [full changelog](https://github.com/retro-trans/ACE/blob/main/docs/CHANGELOG.md).

### Release status

**Further proofreading and a full playthrough are needed.** Mission 3's progression fix was confirmed in play. Earlier builds had confirmation for mission 1 (tutorial and aerial combat), mission 2's briefing, the title screen and the save screen. The menu/HUD corrections, release ending movie and remaining missions still need further in-game review.

Automated checks passed for 3,493 dialogue rows, Japanese text-table inventory, the 35 replaced UI textures, karaoke layout, disc layout and movie scope. The three edited movies preserve all audio and nonvideo bytes; all 22 story movies remain byte-identical to the original. The patch is decoded and the complete output verified before publication. These checks do not certify every emulator, console or gameplay route.

Four credit readings remain provisional: **Mitsuo Hasegawa, Naoizumi Tazo, Rights In and Artprest**. Some fast-moving news shots were re-encoded at lower quality to fit the original movie space. See [movie notes](https://github.com/retro-trans/ACE/blob/main/docs/movies.md).

**Boot the patched ISO fresh and load a normal memory-card save.** Older save states can restore old text, fonts and layout data.

### What's included

English menus, help, names, objectives, briefings, mission dialogue, Terminology entries, UI textures, news captions, ending epilogue and credits, and bilingual opening/ending lyrics with karaoke. Japanese audio is preserved. The 22 story movies and MOVIE005 remain original.

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
