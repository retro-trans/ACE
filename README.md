# Another Century's Episode — English patch

English fan translation of **Another Century's Episode** for PlayStation 2 (**Japan, SLPS-25394**). Apply the downloadable xdelta patch to your own disc image. This repository contains translation text, glossaries, layout metadata and tools.

## Applying the patch

Use [Retro Trans](https://github.com/retro-trans/retro-trans-tools) for automatic patching:

1. Update Retro Trans, click **Refresh catalog**, and open **Automatic**.
2. Select your original Japanese ISO or your public **0.1.32 English ISO**, then **Another Century's Episode**, **English**.
3. Leave Target on **Latest**, choose a new output filename, and apply the patch. The app downloads the matching patch and verifies the result.

See [Releases](https://github.com/retro-trans/ACE/releases) for changes, checksums and known limitations. **Boot the patched image fresh and load a normal memory-card save.** Older save states can restore old text and layout data.

For manual patching:

1. Dump your Japanese disc to an ISO. The full patch requires these exact source bytes:
   - `Another Century's Episode (Japan).iso` — **3,357,147,136 bytes**
   - SHA-256: `7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9`
2. Download `ACE-English-0.1.38.xdelta` from [release 0.1.38](https://github.com/retro-trans/ACE/releases/tag/v0.1.38).
3. Apply it with [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or xdelta3:

   ```text
   xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.38.xdelta "ACE English 0.1.38.iso"
   ```

4. Verify the output: **3,357,147,136 bytes**, SHA-256 `43657b815725eb6007ef8e4fa3254dba385ff6eeaddaaad41b0dc68c68a46fa0`.

To upgrade an existing **0.1.32 English ISO**, refresh the Retro Trans catalog and choose **Latest** or **0.1.38**. For manual upgrading, use `ACE-English-0.1.32-to-0.1.38.xdelta` with that ISO. Its required source SHA-256 is `72d807e7b9e8f02f54b2ff3f491ed0fdb60c4cbf15dabdb81a0195217b248f73` (3,357,147,136 bytes). Both routes produce the same verified 0.1.38 image.

The manifest and validation report accompany every patch. Older supported public builds can upgrade through existing Retro Trans catalog routes. Local test builds are not direct patch inputs; use the original Japanese disc image for those.

## Included in 0.1.38

- English menus, help, unit and pilot names, objectives, briefings, mission dialogue, and the Terminology database.
- English UI textures and variable-width fonts, with text constrained to the game’s measured buffer limits.
- English captions and scrolling statement in the opening news broadcast.
- English ending epilogue, staff credits and producer/publisher cards.
- Romaji karaoke and English lyrics for the Garnet Moon opening and ending song, with the larger ending overlay across the bottom of the credits.
- Mission 3 progression fix: the final Muzura can withdraw correctly. Colored-speaker operator messages use a safer length limit throughout the game.
- Centered difficulty labels, complete controller-diagram labels, and restored AREA OVER and related HUD warnings.
- English title cards and subtitles drawn during playback in all 22 story movies, preserving the original video bytes and reducing patch size.
- 4x dialogue, speaker-name and lock-on fonts sharing the existing dialogue texture allocation; unused Japanese glyphs removed and the main menu atlas reduced by half.
- Corrected fades for all 171 cards in the 22 story movies, removing Japanese flashes around English subtitles.
- Corrected HUD font startup uploads and refreshes on quiet gameplay frames.
- Operator-dialogue drawing capacity expanded from 50 to 128 glyphs to prevent a confirmed memory overflow.
- Full speaker and lock-on names, with the former 12-character drawing limits corrected.
- Single-line briefing conditions and shorter Slot Info weapon labels to avoid clipping.
- Repacked opening, news and ending movies to reduce decoder pauses without re-encoding pictures or changing audio or lyrics.
- Version and retro-trans credit on the title screen.
- Corrected carrier information and launch-panel labels, without split lettering or stretched bars.

MOVIE005 remains original. Original Japanese audio is preserved throughout, including all 25 translated movies. Text-table and texture checks are evidence of the covered resources, not a guarantee that every possible screen has been seen in play.

## Release status

**Further proofreading and a full playthrough are needed.** The mission 3 progression fix was confirmed in play. Earlier builds had confirmation for mission 1, mission 2's briefing, the title screen and save screen. The operator drawing-buffer overflow is confirmed from saved memory and corrected, but fresh-boot gameplay testing is still needed. Mission 23 completion after Jeril retreats remains unverified. The HUD upload/refresh changes also need further appearance and performance checks.

**Movie pacing has been corrected without picture or audio changes.** In an isolated PCSX2 2.8.2 credits replay, decoded playback improved from 29.13 to 29.96 frames/second and gaps over 60 ms fell from 56 to 2 across the same 3,001-frame interval. This is measured improvement, not a guarantee of zero stutter on every system. The new runtime story captions and name-limit fixes passed automated checks but still need fresh-boot gameplay confirmation. Boot the patched ISO fresh and load a normal memory-card save: older emulator states restore old code, allocations and disc state.

Automated checks verify the disc layout, rebuilt files, text limits, translated textures, karaoke layout, movie scope and unchanged movie audio. The patch is decoded locally and the complete result compared with the release image before publication. See the [changelog](docs/CHANGELOG.md) and [release records](docs/releases/0.1.38/).

Four credit readings remain provisional: Mitsuo Hasegawa, Naoizumi Tazo, Rights In and Artprest. See [movie notes](docs/movies.md). Some fast-moving news-broadcast shots were re-encoded at lower quality to fit the original movie space.

## How it was translated

This is a **machine translation**, produced with large language models and reviewed and edited using scene context and a researched glossary. Terminology primarily follows [Akurasu](https://akurasu.net/wiki/Super_Robot_Wars/MX), with documented exceptions. Song work uses lyrics supplied by the project lead and local automatic alignment. Human proofreading and playtesting are welcome.

## Repository layout

- `docs/` — format notes, translation constraints, changelog and release verification records.
- `tools/` — extraction, translation layout, build, movie and verification tools.
- `work/glossary/` — researched names and terms with sources.
- `work/translation/en/` — English-only `*.en.json` exports; Japanese working scripts remain local.
- `work/ui/` — measurements and layout metadata; screenshots remain local.
- `work/output/` — ignored local builds and release packages.
- `incoming/` — ignored outside reference material.

See [CONTRIBUTING.md](CONTRIBUTING.md), [the handoff](docs/HANDOFF.md), [dialogue limits](docs/dialogue.md), [movie notes](docs/movies.md) and [release packaging](docs/RELEASING.md). The development builders require local source exports and, for song movies, separately supplied lyric files; the public source archive is not a ready-to-play game or a self-contained movie rebuild kit.

## Credits

| Role | Contributor |
| --- | --- |
| Project lead and initial playtesting | pow |

Tools build on work from [ACE-3](https://github.com/retro-trans/ACE-3). See [third-party notices](THIRD_PARTY_NOTICES.md).

## License

Original translation text and tools: [MIT](LICENSE). The game and its assets belong to Banpresto / FromSoftware and the respective rights holders. Third-party fonts and supplied song lyrics retain their own rights; the project license does not cover them or the game assets. Bring your own disc image.
