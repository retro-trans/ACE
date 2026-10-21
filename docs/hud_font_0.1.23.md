# Speaker-name 4x font (0.1.23)

Requested on 2026-10-21 using the Torres radio-window screenshot. Speaker names use HUD font 50071 with
texture 50051 in Fe1p/Fe2p, shared with lock-on labels and the full-width English HUD warnings.

`tools/hud_font_hd.py` replaces the 1x English set with Noto Sans JP at 4x texel density, keeping the shipped
13-unit cell, bearings, widths and advances. All 69 speaker names retain identical measured widths. The
95 printable ASCII glyphs occupy rows 17-285 of a 512x512 atlas (previously 256x128). Stock warning pixels
and their metrics, plus the complete original palette, are preserved. No executable changes are made.

The header's texture size, pixel length, TEX0 buffer width and width/height exponents are updated together.
The format remains linear PSMT4HH. Each atlas grows from 16,480 to 131,168 bytes. **The larger GS allocation
needs fresh-boot gameplay verification**; static font proofs cannot establish that it fits the game's runtime
texture allocation. In particular check speaker names, lock-on labels, AREA OVER and surrounding HUD art.

Commands:

```
python tools/verify_hud_hd.py
python tools/verify_hud_hd.py --write
python tools/ui_layout.py check speakers lockon
python tools/build.py 0.1.23 --movies MOVIE001,MOVIE002,MOVIE003
python tools/build.py 0.1.23 --write --movies MOVIE001,MOVIE002,MOVIE003
python tools/verify_hud_hd.py --iso work/output/ACE-EN-0.1.23.iso --write
python tools/japanese_inventory.py work/output/ACE-EN-0.1.23.iso
```

Pre-build checks passed: printable ASCII coverage, 4x glyph height, identical name metrics and warning
pixels/palette; 173 speaker/lock-on rows have zero layout problems. Proofs under `work/ui/hud-font-0.1.23/`
are reconstructed font previews, not emulator captures. Lyrics and the automatic title version remain enabled.
This is a local test build; no release was requested.

Final output: `work/output/ACE-EN-0.1.23.iso`, 3,357,147,136 bytes. SHA-256:
`1410084f4bd46f00eb8dcd30d99f56555730d3e0758179c2c50b59672bbe2446`.
The build's ISO/UDF and payload checks passed. Full resource comparison with 0.1.22 passed: all four HUD
font copies match the expected bytes; all other resources and the executable are unchanged except the
three automatic title-version texture copies. Movie identities are unchanged, including both lyric overlays.
Japanese-table inventory: 0 tables and 0 rows. Evidence: `work/ui/hud-font-0.1.23/verification.json`.

PCSX2 testing was prepared, but another game started in the shared emulator before the test image was ready.
No gameplay verification was performed. The temporary keyboard mappings were restored to the original Pad1
section in the saved PCSX2 configuration; the other running game was left alone. The running emulator may
retain the temporary keyboard mappings until it reloads its settings or restarts.
