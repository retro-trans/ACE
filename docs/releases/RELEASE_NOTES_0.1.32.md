English fan translation of **Another Century's Episode** for PS2 (**Japan, SLPS-25394**), with corrected HUD font uploads and a larger dialogue drawing buffer. Includes all translated movies and opening/ending lyrics.

### Apply

**Recommended:** Use [Retro Trans](https://github.com/retro-trans/retro-trans-tools). Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or public **0.1.29 English ISO**, choose **English** and **0.1.32** (or **Latest**), and select a new output filename. Older supported public builds can upgrade through the catalog's existing routes.

**Manual patching:** Use [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or xdelta3:

| Source image | Patch |
| --- | --- |
| Original Japanese SLPS-25394 ISO | `ACE-English-0.1.32.xdelta` |
| Public 0.1.29 English ISO | `ACE-English-0.1.29-to-0.1.32.xdelta` |

```text
xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.32.xdelta "ACE English 0.1.32.iso"
```

Original image: **3,357,147,136 bytes**, SHA-256 `7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9`.

Public 0.1.29 upgrade source: **3,357,147,136 bytes**, SHA-256 `02ad1831f30daf61348b24cdeb176e1be3bee019cfad7fefcac7a846844f7f6f`.

Release output: **3,357,147,136 bytes**, SHA-256 `72d807e7b9e8f02f54b2ff3f491ed0fdb60c4cbf15dabdb81a0195217b248f73`.

Both patches produce the same output. Local test builds are not upgrade-patch inputs; use the full patch with the original Japanese ISO. Retro Trans handles supported DVD CHD extraction; manual patchers require an unpacked ISO.

`BUILD-MANIFEST.json` records exact source, output and patch identities. `VALIDATION.json` records full patch round trips, and `SHA256SUMS.txt` covers the downloads.

### What changed since 0.1.29

- **HUD lettering:** corrects the startup upload method for the shared 4x font and refreshes its texture on quiet gameplay frames. These changes address scrambled speaker/lock-on lettering and warning banners.
- **Dialogue stability:** expands an undersized operator-dialogue drawing buffer from 50 to 128 glyphs. A saved hang showed a 53-character message overwriting 336 bytes of memory and damaging a graphics packet. Existing translation and layout limits remain unchanged.
- **Credits:** publicly identifies the project lead and playtester as **pow**.

Retains the mission 3 progression fix, corrected menus and carrier/launch panels, AREA OVER warning, title version/group credit, 4x fonts, English text in all 22 story movies, and the opening/ending romaji karaoke and English lyrics. The ending lyrics retain the larger overlay across the bottom of the credits. Movie and lyric data are unchanged from 0.1.29. See the [changelog](https://github.com/retro-trans/ACE/blob/main/docs/CHANGELOG.md).

### Release status

**Further proofreading and a full playthrough are needed.** The drawing-buffer overflow is confirmed from saved memory and corrected in this build, but the affected missions still require fresh-boot gameplay testing. **Mission 23 completion after Jeril retreats remains unverified.** HUD appearance and performance also need further gameplay confirmation.

**Credit-roll microstuttering remains under investigation.** This release does not contain a credit-stutter fix. Offline checks found complete frame counts and regular timestamps, with two packet-scheduling concerns around 2:44; no emulator playback cause has been confirmed.

Automated checks passed for the finished ISO's drawing-buffer allocation and comparison with the preceding local build. Only the intended executable change and title stamps differ from 0.1.31; all other resources, movies and lyrics match. Earlier checks cover the HUD upload/refresh paths, translated text, movie subtitle fades, font data and lyric layout. Both release patches are fully decoded and compared with the target ISO before publication. These checks do not certify every emulator, console or gameplay route.

**Boot the patched ISO fresh and load a normal memory-card save.** Older emulator save states restore old executable code, allocations and potentially corrupted memory, bypassing these fixes.

Four credit readings remain provisional: **Mitsuo Hasegawa, Naoizumi Tazo, Rights In and Artprest**. Some fast-moving news shots were re-encoded at lower quality to fit the original movie space. See [movie notes](https://github.com/retro-trans/ACE/blob/main/docs/movies.md).

### What's included

English menus, help, names, objectives, briefings, mission dialogue, Terminology entries, UI textures, 22 story movies, news captions, ending epilogue and credits, and bilingual opening/ending lyrics with karaoke. Japanese audio is preserved. MOVIE005 stays original.

### How it was translated

This is a **machine translation**, produced with large language models and reviewed and edited using scene context and a researched glossary. Terminology primarily follows Akurasu, with documented exceptions. Human proofreading and playtesting are welcome.

### Acknowledgements

- **Project lead and playtesting:** pow
- Tools and release structure build on [ACE-3](https://github.com/retro-trans/ACE-3) and [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools).

### Source code

English translation exports, glossaries, layout metadata and tools are in the [project repository](https://github.com/retro-trans/ACE). GitHub's source archives contain the repository at the release tag. Use the `.xdelta` assets to patch the game; development rebuilds require local source exports.

### Contribute

Report bugs and translation issues through [GitHub Issues](https://github.com/retro-trans/ACE/issues), including the patch version, mission and reproduction steps.

No complete game images are included. Apply the patch to your own disc image.
