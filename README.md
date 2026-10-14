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
2. Download `ACE-English-0.1.17.xdelta` from [release 0.1.17](https://github.com/retro-trans/ACE/releases/tag/v0.1.17).
3. Apply it with [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or xdelta3:

   ```text
   xdelta3 -d -s "Another Century's Episode (Japan).iso" ACE-English-0.1.17.xdelta "ACE English 0.1.17.iso"
   ```

4. Verify the output: **3,357,147,136 bytes**, SHA-256 `198bfe6cbd177347927aa412e716197f0d148e06ad768ee94537ac39b8e5871c`.

The manifest and validation report accompany every patch. This first public release supports the original Japanese image as its source; local test builds are not patch inputs.

## Included in 0.1.17

- English menus, help, unit and pilot names, objectives, briefings, mission dialogue, and the Terminology database.
- English UI textures and variable-width fonts, with text constrained to the game’s measured buffer limits.
- English captions and scrolling statement in the opening news broadcast.
- English ending epilogue, staff credits and producer/publisher cards.
- Romaji karaoke and English lyrics for the Garnet Moon opening and ending song. The ending uses a larger overlay across the bottom of the credits.

The **22 story movies remain original**, as does MOVIE005. Original Japanese audio is preserved throughout. Text-table and texture checks are evidence of the covered resources, not a guarantee that every possible screen has been seen in play.

## Release status

**Further proofreading and a full playthrough are needed.** Mission 1 (including tutorial and aerial combat), mission 2’s briefing, the title screen and the save screen were confirmed in earlier local builds. The latest opening/ending changes and title transition still need in-game review. Song timings were aligned automatically and still need a listening review.

Automated checks verify the disc layout, rebuilt files, text limits, karaoke layout, movie frame counts and unchanged movie audio. The patch is decoded locally and the complete result compared with the release image before publication. See the [changelog](docs/CHANGELOG.md) and [release records](docs/releases/0.1.17/).

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
