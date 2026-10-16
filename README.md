# Another Century's Episode — English patch

English fan translation of **Another Century's Episode** for PlayStation 2 (**Japan, SLPS-25394**). Apply the downloadable xdelta patch to your own disc image. This repository contains translation text, glossaries, layout metadata and tools.

## Applying the patch

Use [Retro Trans](https://github.com/retro-trans/retro-trans-tools) for automatic patching:

1. Update Retro Trans, click **Refresh catalog**, and open **Automatic**.
2. Select your original Japanese ISO, then **Another Century's Episode**, **English**.
3. Leave Target on **Latest**, choose a new output filename, and apply the patch. The app downloads the matching patch and verifies the result.

See [Releases](https://github.com/retro-trans/ACE/releases) for changes, checksums and known limitations. **Boot the patched image fresh and load a normal memory-card save.** Older save states can restore old text and layout data.

For manual patching:

1. Dump your Japanese disc to an ISO. The full patch requires these exact source bytes:
   - `Another Century's Episode (Japan).iso` — **3,357,147,136 bytes**
   - SHA-256: `7ea891fddbbc3f560330e7c8ecc74e36d2f1137cd1907abf0af3158171b3e3e9`
2. Download `ACE-English-0.1.20.xdelta` from [release 0.1.20](https://github.com/retro-trans/ACE/releases/tag/v0.1.20).
3. Apply it with [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or xdelta3:

   ```text
   xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.20.xdelta "ACE English 0.1.20.iso"
   ```

4. Verify the output: **3,357,147,136 bytes**, SHA-256 `45148f8c96a06d8cc5129de216dcf0f36830cb3f82f4f4f1c82652af79168082`.

The manifest and validation report accompany every patch. This release requires the original Japanese image; earlier English releases and local test builds are not patch inputs. Apply it to your original disc image again when upgrading.

## Included in 0.1.20

- English menus, help, unit and pilot names, objectives, briefings, mission dialogue, and the Terminology database.
- English UI textures and variable-width fonts, with text constrained to the game’s measured buffer limits.
- English captions and scrolling statement in the opening news broadcast.
- English ending epilogue, staff credits and producer/publisher cards.
- Romaji karaoke and English lyrics for the Garnet Moon opening and ending song, with the larger ending overlay across the bottom of the credits.
- Mission 3 progression fix: the final Muzura can withdraw correctly. Colored-speaker operator messages use a safer length limit throughout the game.
- Centered difficulty labels, complete controller-diagram labels, and restored AREA OVER and related HUD warnings.

The **22 story movies** and MOVIE005 remain original. Original Japanese audio is preserved throughout. Text-table and texture checks are evidence of the covered resources, not a guarantee that every possible screen has been seen in play.

## Release status

**Further proofreading and a full playthrough are needed.** The mission 3 progression fix was confirmed in play. Mission 1 (including tutorial and aerial combat), mission 2’s briefing, the title screen and the save screen were confirmed in earlier local builds. The latest menu/HUD changes, release ending movie, and remaining missions still need in-game review.

Automated checks verify the disc layout, rebuilt files, text limits, translated textures, karaoke layout, movie scope and unchanged movie audio. The patch is decoded locally and the complete result compared with the release image before publication. See the [changelog](docs/CHANGELOG.md) and [release records](docs/releases/0.1.20/).

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
| Project lead and initial playtesting | [binhlt0402](https://github.com/binhlt0402) |

Tools build on work from [ACE-3](https://github.com/retro-trans/ACE-3). See [third-party notices](THIRD_PARTY_NOTICES.md).

## License

Original translation text and tools: [MIT](LICENSE). The game and its assets belong to Banpresto / FromSoftware and the respective rights holders. Third-party fonts and supplied song lyrics retain their own rights; the project license does not cover them or the game assets. Bring your own disc image.
