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
2. Download `ACE-English-0.1.29.xdelta` from [release 0.1.29](https://github.com/retro-trans/ACE/releases/tag/v0.1.29).
3. Apply it with [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or xdelta3:

   ```text
   xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.29.xdelta "ACE English 0.1.29.iso"
   ```

4. Verify the output: **3,357,147,136 bytes**, SHA-256 `02ad1831f30daf61348b24cdeb176e1be3bee019cfad7fefcac7a846844f7f6f`.

The manifest and validation report accompany every patch. This release requires the original Japanese image; earlier English releases and local test builds are not patch inputs. Apply it to your original disc image again when upgrading.

## Included in 0.1.29

- English menus, help, unit and pilot names, objectives, briefings, mission dialogue, and the Terminology database.
- English UI textures and variable-width fonts, with text constrained to the game’s measured buffer limits.
- English captions and scrolling statement in the opening news broadcast.
- English ending epilogue, staff credits and producer/publisher cards.
- Romaji karaoke and English lyrics for the Garnet Moon opening and ending song, with the larger ending overlay across the bottom of the credits.
- Mission 3 progression fix: the final Muzura can withdraw correctly. Colored-speaker operator messages use a safer length limit throughout the game.
- Centered difficulty labels, complete controller-diagram labels, and restored AREA OVER and related HUD warnings.
- English title cards and subtitles restored in all 22 story movies.
- 4x dialogue, speaker-name and lock-on fonts sharing the existing dialogue texture allocation; unused Japanese glyphs removed and the main menu atlas reduced by half.
- Corrected fades for all 171 cards in the 22 story movies, removing Japanese flashes around English subtitles.
- Version and retro-trans credit on the title screen.
- Corrected carrier information and launch-panel labels, without split lettering or stretched bars.

MOVIE005 remains original. Original Japanese audio is preserved throughout, including all 25 translated movies. Text-table and texture checks are evidence of the covered resources, not a guarantee that every possible screen has been seen in play.

## Release status

**Further proofreading and a full playthrough are needed.** The mission 3 progression fix was confirmed in play. Mission 1 (including tutorial and aerial combat), mission 2’s briefing, the title screen and the save screen were confirmed in earlier local builds. The latest panel fixes, restored story movies, ending movie and remaining missions still need in-game review. The revised shared font allocation addresses reported speaker/lock-on corruption and passes file checks, but still needs fresh-boot gameplay confirmation. A reported mission 23 completion stall remains under investigation; this release does not claim to fix it.

Automated checks verify the disc layout, rebuilt files, text limits, translated textures, karaoke layout, movie scope and unchanged movie audio. The patch is decoded locally and the complete result compared with the release image before publication. See the [changelog](docs/CHANGELOG.md) and [release records](docs/releases/0.1.29/).

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
