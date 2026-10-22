English fan translation of **Another Century's Episode** for PS2 (**Japan, SLPS-25394**), including English news captions, ending credits and opening/ending karaoke.

### Apply

**Recommended:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO, choose **English** and **0.1.17** (or **Latest**), then choose a new output filename. The app downloads the patch and verifies the result.

**Manual patching:** [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) and [xdelta3](https://github.com/jmacd/xdelta) accept the same patch:

| Source image | Patch |
| --- | --- |
| Original Japanese SLPS-25394 ISO | `ACE-English-0.1.17.xdelta` |

```text
xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.17.xdelta "ACE English 0.1.17.iso"
```

Original image: **3,357,147,136 bytes**; SHA-256 `7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9`.

Release output: **3,357,147,136 bytes**; SHA-256 `198bfe6cbd177347927aa412e716197f0d148e06ad768ee94537ac39b8e5871c`.

This is the first public release. There are no upgrade patches from earlier local test images. `BUILD-MANIFEST.json` records exact source, output and patch identities; `VALIDATION.json` records the successful full patch round trip; `SHA256SUMS.txt` covers the downloads. Retro Trans handles supported DVD CHD extraction; manual patchers require the unpacked ISO.

### What changed

- First public release of the English game text and interface, including the Terminology database, briefings and mission dialogue.
- English captions and scrolling statement in the opening news broadcast.
- English ending epilogue, staff credits and producer/publisher cards.
- Romaji karaoke and English lyrics for Garnet Moon and the ending song. Build 0.1.17 enlarges the ending lyrics across the bottom of the credits with a translucent backing and replaces the opening epilogue text directly with an English scroll.
- Retains the text limits and layout fixes tested during local development. See the [full changelog](https://github.com/retro-trans/ACE/blob/main/docs/CHANGELOG.md).

### Release status

**Further proofreading and full in-game playtesting are needed.** Mission 1 (tutorial and aerial combat), mission 2's briefing, the title screen and save screen were confirmed in earlier local builds. The latest opening/ending changes, title transition and other missions still need in-game testing. Song timings were aligned automatically and need a listening review.

Four staff/company readings are provisional: **Mitsuo Hasegawa, Naoizumi Tazo, Rights In and Artprest**. A few fast-moving news-broadcast shots were re-encoded at lower quality to fit the original movie space. See the [movie notes](https://github.com/retro-trans/ACE/blob/main/docs/movies.md).

Automated checks found no remaining Japanese in the inspected text tables or the 35 replaced UI textures. All 52 karaoke rows passed layout checks, all 1,920 epilogue frames passed the source-lettering check, and opening/ending frame counts match the originals. Disc layout, rebuilt file hashes and unchanged movie audio/nonvideo data were verified. These checks do not certify every emulator, console or gameplay route.

**Boot the patched ISO fresh and load a normal memory-card save.** Older save states can restore old text, fonts and layout data.

### What's included

English menus, help, names, objectives, briefings, supported mission dialogue, Terminology entries, UI textures, news captions, ending epilogue and credits, and bilingual opening/ending lyrics. Japanese audio is preserved.

The **22 story movies are intentionally original and untranslated**. MOVIE005 is also unchanged. Only MOVIE001, MOVIE002 and MOVIE003 receive movie edits.

### How it was translated

This is a **machine translation**, produced with large language models and then reviewed and edited using scene context and a researched glossary. Terminology primarily follows Akurasu, with documented exceptions. Song work uses lyrics supplied by the project lead and local automatic alignment. Human proofreading and playtesting are welcome.

### Acknowledgements

- **Project lead and initial playtesting:** pow
- Tools and release structure build on [ACE-3](https://github.com/retro-trans/ACE-3) and [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools).

### Source code

English translation exports, glossaries, layout metadata and tools are in the [project repository](https://github.com/retro-trans/ACE). GitHub's source archives contain the repository at the release tag. Use the `.xdelta` asset to patch the game. Development rebuilds require local source exports and separately supplied song lyrics.

### Contribute

Report bugs and translation issues through [GitHub Issues](https://github.com/retro-trans/ACE/issues), including the patch version, mission and reproduction steps. Proofreading and playtesting are welcome.

No complete game images are included. Apply the patch to your own disc image.
