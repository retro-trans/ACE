# Release packaging

Repository: https://github.com/retro-trans/ACE. Publish with the project lead’s explicit authorization. Use the ACE-3 README/release structure and the [Retro Trans release standard](https://github.com/retro-trans/retro-trans-tools/blob/main/docs/RELEASE_STANDARD.md).

Stable identity: game `ace`, platform `PS2`, edition `English`, language `en`. The initial public version is `0.1.17`; its only supported source is the original Japanese SLPS-25394 ISO. Published patch bytes and output identities are immutable.

## Prepare and verify

1. Complete the build and game-specific checks described in [HANDOFF.md](HANDOFF.md). Record actual playtesting separately from automated checks.
2. Run `python tools/strip_jp.py`, audit the staged files, and commit the reviewed English-only sources. Keep private lyrics, Japanese scripts, source assets and disc images out of Git.
3. Check out Retro Trans Tools at `dde06f13fdabd7d9fa03af861f50e72fcf196faa` under ignored `work/source/retro-trans-tools`. This is the upstream revision reviewed for 0.1.17.
4. With Python 3.11 or later, preview `py -3.11 tools/package_release.py --version 0.1.20 --source-commit <full-commit>`, then repeat with `--write`. The script uses upstream’s bundled verified xdelta engine and release builder. It hashes both images, creates the patch, decodes it and verifies the entire output, checks that inputs did not change, and adds SHA-1 identifiers for supported DVD CHD identification. Substitute the explicitly authorized version for future releases.
5. The final package is `work/output/release-0.1.20/`. It must contain exactly the listed patches, `BUILD-MANIFEST.json`, `VALIDATION.json` and `SHA256SUMS.txt`. Canonical metadata is copied to `docs/releases/0.1.20/`. A private local configuration stays under `work/source/`.
6. Include a direct upgrade from the previous public release. Use `py -3.11 tools/add_release_upgrade.py --version <target> --from-version <previous>` and repeat with `--write`. It verifies both published image identities, round-trips the new patch, and writes a separate augmented package while preserving existing patch bytes. Use the augmented package for publication. Test `verify_release_routes.py` with `--upgrade-from <previous>` as well as original-disc routes.

The source commit identifies the translation and packaging sources. A later commit may add the resulting release metadata and publication evidence without changing game bytes.

## Publish

Stage a draft GitHub release at the matching version tag, upload the patch, validation report and checksums, then upload the manifest last. Compare every uploaded size and SHA-256 with the local asset. Publish a regular release (the Automatic catalog excludes GitHub prereleases), while clearly describing the work-in-progress playtesting status in its notes.

Dispatch the Retro Trans Tools **Refresh patch catalog** workflow with `repository=retro-trans/ACE`. Confirm successful validation and public catalog discovery. Use `tools/verify_release_routes.py --version 0.1.20 --catalog <downloaded-catalog> --out <report>` to check original-disc Latest/specific-version routes, current-image no-op, and unknown-image rejection. Next version only may select an earlier published release. Keep workflow and route evidence in the release record.

Never upload a complete game image, extracted movie/audio or private build configuration. Never replace published patch bytes or change a version's output image; use a new version for a changed build. An authorized repair of a missing upgrade route may add a new patch to the existing release and update its manifest, validation report and checksums. Preserve the prior metadata as evidence, verify all existing patch records are unchanged with the catalog's immutability check, upload the new patch first and the manifest last, and refresh/verify the public catalog. This changes delivery routes only, not the game build.
