# Launch information panel fix, 0.1.26

The user reported a repeated fragment after `Resources` and a horizontal smear after `Repair Eff.` on the
Launch Setting screen on 2026-10-21. The two labels are baked into `t0802.tm2`, a 256x128 atlas.

`b081.mnb` objects 21 and 23 map parts of each card repeatedly/reversed to extend it horizontally. Resource
UVs are at `0x23a0`, with x boundaries 107.4253 and 91.6326; repair UVs at `0x2550` use 93.0355 and 91.0208.
The old English labels extended into those regions. Reconstructing the encoded texture through those UVs
reproduces the user's screenshot artifacts.

`b083.mnb` also uses the labels in unit setup. Its corresponding UV tables at `0x3120` and `0x32c0` constrain
the safe drawing width further (the repair label's left region ends at x=88.087). The new Resources drawing
box is `[23,7,86,24]`; Repair Eff. is `[22,59,85,76]`. Both retain height 18 and full wording, with horizontal
growth removed. Separate `erase_box` bounds remove the complete original text. Armor, Repair Res., the percent
sign and other artwork are unchanged; neither mesh is edited.

## Reproduce

```text
python tools/launch_panel_spec.py
python tools/launch_panel_spec.py --write
python tools/verify_launch_panel.py
python tools/verify_launch_panel.py --write
python tools/build.py 0.1.26
python tools/build.py 0.1.26 --write
python tools/verify_launch_panel.py --iso work/output/ACE-EN-0.1.26.iso --write
python tools/japanese_inventory.py work/output/ACE-EN-0.1.26.iso
```

Do not restrict movie selection: all 25 translated movies, including both lyric overlays, remain enabled.
The verifier permits only this texture and the automatic title-version texture to differ from 0.1.25.
It checks standalone and packed copies, other game resources and all remaining disc files byte for byte.
Proofs and UV coordinates are saved under `work/ui/launch-panel-0.1.26/`; the panels are reconstructed artwork,
not emulator screenshots, and omit the dynamic numeric values. In-game confirmation remains necessary.

Completed ISO: `work/output/ACE-EN-0.1.26.iso`, 3,357,147,136 bytes, SHA-256
`95b7fafe2b4c5ddbfbd276f1322cb4cc08479891af0b714db3520b481472244c`.
Build layout/payload checks and final resource comparison passed. Three copies of the corrected texture
(standalone, MenuCampaign, MenuFree) and three title-version copies match the intended encoding. All other
game resources and disc files, including both meshes, the carrier fix, movies and audio, match 0.1.25 byte
for byte. The Japanese-table inventory found 0 tables and 0 rows. Evidence is in
`work/ui/launch-panel-0.1.26/verification.json`; logs are beside the ISO.
In-game confirmation remains necessary. No release was requested.
