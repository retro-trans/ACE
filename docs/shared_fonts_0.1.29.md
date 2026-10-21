# Shared English fonts (0.1.29)

The user reported blocks in multiple radio speaker names and in lock-on labels after
the 4x HUD change, then requested removal of Japanese glyphs. No emulator was controlled.
This build addresses the expanded HUD texture's memory use; runtime confirmation remains
necessary. It does not claim to fix the separate mission 23 completion stall.

## Evidence and placement

The original HUD texture is 256x128 PSMT4HH. Build 0.1.23 enlarged it to 512x512 without
changing its fixed GS base. PSMT4HH stores its four-bit texels in the high nibble of
32-bit words: that expansion increases the covered address space from 128 KiB to 1 MiB.
Static glyph previews could not detect corruption from other runtime uploads.

The executable's resource initializer at EE 0x1c45d0 reads the table at 0x2a64d0:

| Resource | Original GS texture base | Palette base |
| --- | --- | --- |
| 50050 (dialogue) | 0x2600 | 0x3ff4 |
| 50051 (HUD) | 0x0c00 | 0x3fff |

0.1.29 changes the HUD texture-base word at 0x2a64d8 to 0x2600. It retains both
palette bases. Both texture resources now contain identical pixel data, so loading
either cannot overwrite the other font's lettering. Each resource retains its own
palette and each CCM points to its own glyph rectangles. The existing dialogue
allocation remains 1024x512 PSMT4, GS-swizzled transfer mode 1, occupying 256 KiB.
The game already uses this format, size and transfer mode for dialogue.

Dialogue English occupies rows 22-241; HUD English occupies rows 259-418. Required
stock symbols occupy separate rows before each set. Neither font overlaps the other.
Both fonts have four texels per screen unit, with the previous ASCII bearings, widths,
advances and padding preserved. No mission script, message token or text is changed.

## Japanese glyph removal

The previous HUD rebuild already erased Japanese pixels but left obsolete glyph records.
The dialogue and main menu fonts still retained Japanese lettering. `english_fonts.py`
now removes unused kana/kanji pixels, mapping entries and unreferenced records. Required
punctuation, full-width Latin letters/digits, symbols and warning lettering remain.
The main menu font is repacked into 1024x512 instead of 1024x1024 (half the pixel storage).
The small-name font's unused records are also removed. English widths remain unchanged.

Diagnostic builds retain the legacy dialogue-font path when Japanese dialogue is requested.
Do not regenerate the separate 0.1.27 mission diagnostic with a Japanese-free font.

## Verification and testing

```text
python tools/build.py 0.1.29 --write
python tools/verify_shared_fonts.py work/output/ACE-EN-0.1.29.iso
python tools/japanese_inventory.py work/output/ACE-EN-0.1.29.iso
```

The verifier checks all four in-game bundle copies, font metrics, required warning pixels,
shared pixels, separate palettes, Japanese glyph removal, and permitted resource changes
against 0.1.28. It checks the executable differs only in the single texture-base word.
Movie hashes must match 0.1.28, including its subtitle fade correction and both songs;
the build independently reads the movie bytes back from the ISO.

For gameplay confirmation, boot the new ISO fresh and load a normal memory-card save.
An old emulator save state can restore old font textures/code. Check Bright/Torres and
enemy speaker names, lock-on labels, AREA OVER, and surrounding HUD graphics. Runtime
confirmation is not implied by the reconstructed font previews.

The user subsequently requested release 0.1.29 on 2026-10-22; see the release notes
for the distinction between automated verification and outstanding gameplay testing.

## Completed output

`work/output/ACE-EN-0.1.29.iso`, 3,357,147,136 bytes, SHA-256
`02ad1831f30daf61348b24cdeb176e1be3bee019cfad7fefcac7a846844f7f6f`.
The final comparison passed for all four in-game bundles and every changed menu/name
font, with no unrelated resource or executable changes. All 25 movie hashes match
0.1.28 and both lyrics are included. Japanese-table inventory: 0 tables, 0 rows.
DATA.BIN decreased by 1,132,544 bytes; the disc image retains its standard padded size.
Reports and reconstructed font proofs are in `work/ui/hud-speaker-0.1.29/`.
