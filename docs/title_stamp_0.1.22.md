# Title version and group credit (0.1.22)

Requested on 2026-10-17, using the SRW Z title screenshot as a visual reference. The ACE title now has two
small, right-aligned lines at the bottom right: `v0.1.22` and `github.com / retro-trans`. Light lettering with
a dark outline keeps the credit readable over the title background. The original copyrights stay intact.

## Implementation

- `tools/title_stamp.py` adds the lettering to the translated `t3105.tm2` atlas before final palette encoding.
  It uses Noto Sans JP at a 9-pixel design size, weight 600, supersampled at 4x, with a dark one-pixel outline.
- `build.py` passes its version to `TextureText`. The label is generated per build, so future versions update
  automatically. The build report records the version, group text, atlas bounds and screen bounds.
- The copyright sprite is record 1 at `l014.mnl + 0x48`, with a 56-byte record stride after the 16-byte header.
  Originally it maps atlas `[0,440,448,512]` to screen `[32,364,480,436]`. Two integers change: its right
  screen offset at `0x58` from 224 to 256, and its UV right edge at `0x70` from 448 to 480. The resulting
  screen rectangle is `[32,364,512,436]`, still with exact 1:1 pixel mapping and unchanged left/top position.
- Version ink bounds: atlas `[434,482,468,491]`, screen `[466,406,500,415]`.
- Group ink bounds: atlas `[370,498,468,510]`, screen `[402,422,500,434]`.
- Both lines have a 12-pixel right margin in the native 512x448 title layout. The group has a 14-pixel bottom
  margin. They use previously transparent pixels; existing title/copyright artwork is preserved.
- Texture dimensions, headers and palette remain unchanged. Standalone resources and bundled copies are
  replaced together. The menu logic and executable are unchanged.

## Verification

`python tools/verify_title_stamp.py --version 0.1.22` checks the proposed artwork without writing files.
Add `--write` for reconstructed static title/footer previews and a coordinate report under
`work/ui/title-stamp-0.1.22/`. These are layout proofs, not emulator screenshots.

Build after a dry run with `python tools/build.py 0.1.22 --write --movies MOVIE001,MOVIE002,MOVIE003`.
The song lyrics remain included. Then run
`python tools/verify_title_stamp.py --version 0.1.22 --iso work/output/ACE-EN-0.1.22.iso --write`.
This checks every DATA.BIN resource against 0.1.20, permitting only the title texture, layout and their packed
copies to differ. It also checks the unchanged executable and movie identities, every title pixel outside
the stamp, and the expected version in the build report. Run the normal Japanese-table inventory afterward.

Fresh-boot title-screen confirmation remains for user testing. No release was requested for this build.

## Completed build checks

- ISO: `work/output/ACE-EN-0.1.22.iso`, 3,357,147,136 bytes; SHA-256
  `2030fc1dddce477c80aa1b7692ad80164eefe4c3408e500dd6dddbc3807deb7d`.
- The final ISO comparison passed: three copies each of the title texture and layout are correct.
  Only standalone `t3105.tm2`, standalone `l014.mnl`, `MenuTitle.csc` and `MenuTitleIntro.csc` differ
  from 0.1.20. All other resources, executable bytes and movie identities are unchanged.
- The packed layout's original bytes differ from the standalone layout at `0x308`, `0x310` and `0x318`.
  Verification preserves each copy's own original data and permits only the two copyright-bound changes.
- 1,070 atlas pixels changed, all inside the new lettering bounds. Existing artwork and palette are intact.
- Japanese-table inventory: zero tables and zero rows. Reconstructed title/footer previews were inspected;
  an emulator fresh-boot check remains pending.
