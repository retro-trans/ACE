# Carrier information panel, 0.1.25

The user reported split text and values overlapping labels in the Rendezvous Point upgrade screen on
2026-10-21. The affected artwork is `t0403.tm2`, a 256x256 texture shared by the carrier panel and left menu.

## Cause and correction

Object 32 of `b043.mnb` maps the panel across three horizontal sections. Its UV table begins at file offset
`0x2f50`. The left strip samples x=0.1587..94.2618; the wide middle section samples the very narrow, reversed
strip x=94.2618..94.1005; the right border samples x=94.1005..118.103. The vertical range is y=0.8986..167.3242.
The old translation extended English letters into that middle strip and the right border. The resulting
stretch explains both the detached final letters and the gray bars behind dynamic values.

Six labels now fit in the fixed left section:

| Label | Drawing box | Change |
| --- | --- | --- |
| Carrier Info | 21,4..90,24 | remove growth; erase original 21,4..94,24 separately |
| Carrier | 14,36..86,56 | remove redundant `Name` and growth |
| Squad | 14,60..86,79 | remove redundant `Name` and growth |
| Units | 13,85..86,103 | remove growth |
| Repair Res. | 14,109..86,128 | fit in fixed column |
| Repair Eff. | 14,132..86,152 | fit in fixed column |

The mesh, dynamic values, font choices, palette and left upgrade controls are unchanged. The renderer's new
optional `erase_box` separates removal of the original heading from the narrower English drawing bounds.

## Reproduction and verification

```text
python tools/carrier_panel_spec.py
python tools/carrier_panel_spec.py --write
python tools/verify_carrier_panel.py
python tools/verify_carrier_panel.py --write
python tools/build.py 0.1.25
python tools/build.py 0.1.25 --write
python tools/verify_carrier_panel.py --iso work/output/ACE-EN-0.1.25.iso --write
python tools/japanese_inventory.py work/output/ACE-EN-0.1.25.iso
```

Build without a movie restriction to retain all 25 translated movies and both lyric overlays.
The verification checks the actual UVs, unchanged pixels in the stretched strip/right border, unchanged
left upgrade artwork, and encoded texture copies. Its ISO comparison allows only the carrier texture and
automatic title-version update; all other resources and other disc files, including movies, must match
0.1.24 byte for byte. Proofs are reconstructed from encoded artwork and saved in
`work/ui/carrier-panel-0.1.25/`; runtime confirmation remains necessary.

Completed ISO: `work/output/ACE-EN-0.1.25.iso`, 3,357,147,136 bytes, SHA-256
`4cf79a34ff43d8d1e0f166f69330352c3128d3f2d5a69f52ba012688f5137b7c`.
Build layout/payload checks and final resource comparison passed. Both carrier-texture copies (standalone
and `MenuCampaign.csc`) and the three title-version copies match the intended encoding. All other resources
and disc files, including the mesh, executable, all 22 translated story movies and both lyric-bearing movies,
match 0.1.24 byte for byte. The final Japanese-table inventory found 0 tables and 0 rows.
Evidence: `work/ui/carrier-panel-0.1.25/verification.json`; logs are beside the ISO. In-game confirmation of
the carrier screen remains necessary; this local build was not released.
