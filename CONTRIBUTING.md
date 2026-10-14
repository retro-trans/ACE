# Contributing

Report translation errors or gameplay problems in [Issues](https://github.com/retro-trans/ACE/issues). Include the patch version, emulator/version or console, mission and scene, and steps to reproduce. A screenshot and the expected wording help. Never attach game images, extracted scripts or save states containing game data.

Read [AGENTS.md](AGENTS.md), [BASE_RULES.md](BASE_RULES.md) and [the handoff](docs/HANDOFF.md) before changing the translation. Follow the glossary and preserve control codes. The byte and line limits in [dialogue.md](docs/dialogue.md) and the layout tools reflect crashes observed in play; do not increase them without proving the relevant buffers can handle it.

The checked-in translation files are English-only exports. Original Japanese scripts and working JSON files stay local. Use your own disc with the extraction/preparation tools described in the format notes; those are developer workflows, not one-step rebuild commands. Movie rebuilds also require local source frames, font dependencies and separately supplied lyrics. Review each tool’s inputs before running it.

Run `python tools/strip_jp.py` before staging translation changes and commit only the resulting `*.en.json` files. Review remaining Japanese: names and short UI terms are allowed; dialogue, narrative source scripts and song lyric files are not. Keep screenshots, source dumps and built media local. Update the changelog and use a new `0.x.y` version for each changed build.

Publishing requires an explicit request from the project lead. Follow [RELEASING.md](docs/RELEASING.md); release patch files and verified metadata only.
