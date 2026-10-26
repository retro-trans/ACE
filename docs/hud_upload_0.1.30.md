# HUD font upload correction (0.1.30)

**Follow-up:** pow confirmed scrambled warning banners after a fresh boot of
this build. Correct startup transfers alone did not maintain the atlas during
gameplay. See `hud_refresh_0.1.31.md` for the missing per-frame refresh.

On 2026-10-26, pow reported a scrambled enemy name in the lock-on label and
confirmed this was 0.1.29 after a fresh boot, not an old emulator save state.
The preceding static atlas checks did not cover the game's upload call sites.

## Reproduced mismatch

The shared dialogue/HUD textures in 0.1.29 are 1024x512 PSMT4, stored in mode 1:
their bytes are arranged for a 512x128 PSMCT32 upload, then sampled as PSMT4.
The HUD is loaded at mission startup by two explicit calls:

| Call site | 0.1.29 target | Required target |
| --- | --- | --- |
| EE 0x1e165c | 0x17c530 (linear upload) | 0x17d1d0 (swizzled upload) |
| EE 0x1e17ec | 0x17c530 (linear upload) | 0x17d1d0 (swizzled upload) |

The linear routine does not read the texture's mode word. It sends the packed
data directly as PSMT4, starting with a 1024x256 transfer and buffer width 16.
That interprets the swizzled bytes as linear texels. Merely setting mode 1 in
the file does not select the correct routine at these call sites.

`tools/font_upload.py` executes the actual integer instructions from the ELF
up to the first `sceGsSetDefLoadImage` call. It rejects the published 0.1.29
startup path. With the two JAL targets changed, both paths produce PSMCT32,
512x128, buffer width 8, at the existing shared base 0x2600. These dimensions
and format match the font's stored bytes and the dialogue uploader.

## Change and verification

`build.py` changes those two calls only when the shared font is enabled.
The atlas, glyph maps, spacing, palettes and shared GS base are unchanged.
No mission text or logic is changed. Diagnostic builds retain the original path.

`verify_shared_fonts.py` now checks both calls and traces their transfer setup
in addition to font resources, glyph metrics, warning symbols, allowed executable
changes, and movie/lyric preservation. Reproduction evidence is in
`work/ui/hud-upload-0.1.30/upload-trace.json`.

The instruction trace verifies upload setup, not complete game execution or
the lifetime of the texture in VRAM. No desktop control or emulator gameplay
was performed. Fresh-boot confirmation is still required for lock-on names,
radio speaker names, dialogue, and AREA OVER. This is a local test build;
publication has not been requested. Mission 23 remains a separate investigation.

## Completed local build

`work/output/ACE-EN-0.1.30.iso`, 3,357,147,136 bytes, SHA-256:
`f608d4e320e5d95506ed3f950640d99a6d371f69c0c0285d89adfb2a27d1efa0`.

The final disc passes font/resource checks and both upload traces. The original
256x128 PSMT4HH font also passes the linear-path control. Comparison with 0.1.29
confirms only the two executable words and three title-version texture copies
changed. All font bytes and other game resources are identical; all 25 movie
hashes and both lyric overlays are retained. The build reads back its movie
payloads and checks ISO/UDF extents. Japanese-table inventory: zero tables/rows.

Evidence: `work/ui/hud-upload-0.1.30/scope-verification.json`,
`work/ui/hud-speaker-0.1.30/verification.json`, and the
`work/output/ACE-EN-0.1.30-*-check.log` files. These remain offline checks;
fresh-boot gameplay confirmation is outstanding.
