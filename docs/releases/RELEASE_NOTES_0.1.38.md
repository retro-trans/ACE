English fan translation of **Another Century's Episode** for PS2 (**Japan, SLPS-25394**). This release reduces patch size, improves movie playback and fixes clipped names and menu text. All translations and opening/ending lyrics are retained.

The original-disc patch is **320 MB**, down from **891 MB** in 0.1.32 (about **64% smaller**).

### Apply

**Recommended:** Use [Retro Trans](https://github.com/retro-trans/retro-trans-tools). Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or public **0.1.32 English ISO**, choose **English** and **0.1.38** (or **Latest**), and select a new output filename. Older supported public builds can upgrade through existing catalog routes.

**Manual patching:** Use [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or xdelta3:

| Source image | Patch | Download |
| --- | --- | --- |
| Original Japanese SLPS-25394 ISO | `ACE-English-0.1.38.xdelta` | 320 MB |
| Public 0.1.32 English ISO | `ACE-English-0.1.32-to-0.1.38.xdelta` | 649 MB |

The upgrade is larger because it restores original story movies from the older re-encoded versions. If you have the original Japanese ISO available, that route uses the smaller download.

```text
xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.38.xdelta "ACE English 0.1.38.iso"
```

All three image identities below are **3,357,147,136 bytes**:

- Original Japanese source SHA-256: `7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9`
- Public 0.1.32 upgrade source SHA-256: `72d807e7b9e8f02f54b2ff3f491ed0fdb60c4cbf15dabdb81a0195217b248f73`
- Release output SHA-256: `43657b815725eb6007ef8e4fa3254dba385ff6eeaddaaad41b0dc68c68a46fa0`

Both patches produce the same output. Local test builds are not upgrade-patch inputs; use the full patch with the original Japanese ISO. Retro Trans handles supported DVD CHD extraction; manual patchers require an unpacked ISO.

`BUILD-MANIFEST.json` records exact source, output and patch identities. `VALIDATION.json` records full patch round trips, and `SHA256SUMS.txt` covers the downloads.

### What changed since 0.1.32

- **Smaller patch, original story-video quality:** restores the original video bytes in all 22 story movies and draws their 171 English captions and title cards during playback. Corrected coverage of the Japanese subtitle fades is retained.
- **Smoother movie playback:** moves excessive padding out of video data in the news, opening and ending movies. This does not re-encode pictures or change audio, timestamps or lyrics. Every decoded frame was compared with the previous version: all 23,782 frames match. In an isolated PCSX2 2.8.2 credits replay, the same interval improved from 29.13 to 29.96 decoded frames/second; gaps over 60 ms fell from 56 to 2.
- **Complete target names:** raises the lock-on drawing capacity from 12 to 24 characters and enlarges its buffer to match. Names such as Jonathan's Grancher no longer hit the old 12-character limit.
- **Complete speaker names:** raises the radio name drawing limit from 12 to 22 characters, addressing names such as Titans Soldier. Font size and the existing safe allocation are preserved.
- **Briefing conditions:** fixes the incomplete “Escort the” objective and two other conditions that wrapped onto an invisible second line. Victory and defeat conditions are now validated as single-line text.
- **Slot Info:** shortens weapon-stat labels to Power and Reload so they fit before the stat bars.

Retains the mission 3 progression fix, larger operator-dialogue buffer, corrected HUD font uploads, menus, carrier/launch panels, AREA OVER warning, title version/group credit and 4x fonts. **Opening and ending romaji karaoke and English lyrics remain included**, with the larger ending lyric area across the bottom of the credits. See the [changelog](https://github.com/retro-trans/ACE/blob/main/docs/CHANGELOG.md).

### Release status

**This remains a work in progress: further proofreading and a full playthrough are needed.** Mission 23 completion after Jeril retreats remains unverified. The runtime story captions and new name limits passed automated checks but still need fresh-boot gameplay confirmation. The credits test demonstrates improvement in the tested emulator setup, not zero stutter on every system.

Automated checks cover runtime subtitle rendering, all 104 lock-on labels, all 69 speaker labels, 801 briefing rows, movie frame/audio preservation and the scope of each local build change. Both release patches are fully decoded and compared with the target ISO before publication. These checks do not certify every emulator, console or gameplay route.

**Boot the patched ISO fresh and load a normal memory-card save.** Older emulator save states restore old executable code, allocations and disc state, bypassing fixes.

Four credit readings remain provisional: **Mitsuo Hasegawa, Naoizumi Tazo, Rights In and Artprest**. Some fast-moving news shots were re-encoded at lower quality in earlier builds to fit the original movie space; this release's repacking introduces no further quality loss. See [movie notes](https://github.com/retro-trans/ACE/blob/main/docs/movies.md).

### What's included

English menus, help, names, objectives, briefings, mission dialogue, Terminology entries, UI textures, 22 story movies, news captions, ending epilogue and credits, and bilingual opening/ending lyrics with karaoke. Japanese audio is preserved. MOVIE005 stays original.

### How it was translated

This is a **machine translation**, produced with large language models and reviewed and edited using scene context and a researched glossary. Terminology primarily follows Akurasu, with documented exceptions. Human proofreading and playtesting are welcome.

### Acknowledgements

- **Project lead and playtesting:** pow
- Tools and release structure build on [ACE-3](https://github.com/retro-trans/ACE-3) and [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools).

### Source code

English translation exports, glossaries, layout metadata and tools are in the [project repository](https://github.com/retro-trans/ACE). GitHub's source archives contain the repository at the release tag. Use the `.xdelta` assets to patch the game; development rebuilds require local source exports and separately supplied lyric files.

### Contribute

Report bugs and translation issues through [GitHub Issues](https://github.com/retro-trans/ACE/issues), including the patch version, mission and reproduction steps.

No complete game images are included. Apply the patch to your own disc image.
