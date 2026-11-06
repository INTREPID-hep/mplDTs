# T-031 — CMS preset remainder and orientation-based phi/eta plotting

- **Status:** proposed
- **Phase:** 3
- **Epic:** E3 Assemblies and extras
- **Depends on:** T-030
- **Branch:** `feature/phase-3-assemblies`
- **PR:** —
- **Owner:** unassigned
- **Labels:** model, plotting, cms

## Context

The CMS virtual frames already exist: `_add_plotting_frames` in
`mpldts/geometry/station.py` registers `StationNvPhi`, `StationNvEta`,
`SectorRef` (including the MB4 sectors 13/14 sign correction) and
`SL13Center` on every CMS chamber. They are welded to the CMS constructor,
so a custom station would get frames it does not have.

Plotting chooses the faceview by convention: `dt_station_patch.py:120,142,169`
treat `super_layer.number == 2` as "the eta layer", which is a CMS layout
fact, not geometry.

## Scope

- Move the CMS virtual frames out of `station.py` into the CMS preset (a
  small function/module next to `sources/cms_xml.py`) and apply it only to CMS
  chambers. Custom stations keep the plain frames.
- Decide phi/eta in the patches from the geometry (the SL pose/normal) or an
  explicit super-layer argument; `faceview=` stays accepted.
- Leave the segment convention (`seg.sl == 2`) working; document it as a
  segment rule, not a station rule.

## Out of scope

- Rewriting the patch layer or its artist structure.
- Image comparison tests.

## Acceptance criteria

- [ ] `StationNvPhi`, `StationNvEta`, `SectorRef` and `SL13Center` resolve exactly
      as before for all 250 CMS chambers (slow sweep).
- [ ] A custom station without CMS frames plots in both views.
- [ ] phi/eta follows the geometry; `faceview="eta"` still works.
- [ ] CMS patch rectangles are unchanged (compare on the 18-case fixture).

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow
```

## Risks / notes

- A wrong orientation rule is invisible in a smoke test; compare against
  `DTStationPatch` output before and after, per chamber and faceview.
