# T-052 — VolumeSink + TgSink + .tg parity

- **Status:** done
- **Phase:** 5
- **Epic:** E5 Authoring and export
- **Depends on:** T-030 (done)
- **Branch:** `feature/phase-5-authoring`
- **PR:** — (branch pushed; the maintainer merges)
- **Owner:** —
- **Labels:** export, backend-seam
- **Completed:** 2026-11-08

## Context

The simulator writes .tg files with a CMS-aware script that walks the legacy
`Station` API and hardcodes the geometry knowledge (one cell volume per super
layer, the SL2 rotation, the honeycomb between SL1 and SL2). The refactor has to
show that the same file comes out of the spec/node tree through a backend seam,
without pyg4ometry and without the core learning the .tg format.

## What was delivered

- `mpldts/export/base.py`: `VolumePlacement`, the `VolumeSink` protocol
  (`begin` / `place` / `end`), the `iter_volume_placements` walk that folds
  grouping nodes (super layer, layer) into the next physical placement and
  visits attachments after the cells, `export_volumes` and a `RecordingSink`.
- `mpldts/export/tg.py`: `TgSink` writes `:SOLID` / `:VOLU` / `:ROTM` / `:PLACE`
  lines, one file per export, into a path or any stream. Box and tube solids;
  a tube's +z solid axis is turned onto the shape axis by the placement
  rotation. Volumes are cached by (name, shape) and rotation matrices by value,
  so a super layer is defined once. Copy numbers are counted per mother.
- Cell material plumbing: `CellGrid.material` (optional), validation, the
  CMS source sets `GasMixture`, `build_station` puts it on the cell node. A
  physical node without a material is a `TgFormatError`, not a silent G4_AIR.
- `test/geometry/test_export.py` (11 tests).

## Parity result

`station_W0_Sec1_St1.tg` from `generate_geometry_data.py` and the file exported
from the spec are the same document:

| | reference | exported |
|---|---|---|
| placements | 621 | 621 |
| placed solids (kind + dimensions) | identical | identical |
| materials | identical | identical |
| rotation matrices | identical | identical |
| position, worst difference at 1e-4 cm | — | 0.0 cm |

Only the names and the comments differ: the exported cell volumes are
`DriftCell_<station>_<SL>` instead of `DriftCell_<w>_<sec>_<st>_SL<n>_<layer encoding>`,
and the honeycomb copy number no longer collides with the first cell (the
reference generator places both at copy 1 when `include_honeycomb` is on).

## Out of scope

- The yoke: boolean `UNION`/`SUBTRACTION` stays in the simulator (ADR-017).
- Switching `generate_geometry_data.py` to the sink, and pinning the downstream
  version: that is T-005, after the merge.
- pyg4ometry and GDML (T-060).
- Writing `world` and `R0`: they belong to the document that includes the
  station files (`geometry_concentrator_template`).

## Acceptance criteria

- [x] The walk emits one placement per solid node and folds the grouping frames.
- [x] Attachment (honeycomb) placements are emitted like any other volume.
- [x] A CMS station exports to .tg that matches the current generator's output.
- [x] The exported placements put every cell on its XML `GlobalPosition`
      (`1e-3` cm) once the station pose is applied.
- [x] No backend dependency; `mpldts.export` is not imported by the core.

## Verification

```python
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_export.py
PYTHONPATH=/home/destrada/mplDTs pytest -q
```

The reference-file test skips when the simulator checkout is absent; set
`MPLDTS_TG_REFERENCE` to any station file to run it elsewhere.

## Risks / notes

- Names are qualified by the exported root, so two station files can be
  included in one `.tg` document without redefining a volume or a rotation.
- A .tg file is a flat list of placements: the hierarchy (super layer, layer)
  is lost on purpose, exactly as in the current generator.
- The yoke's `SUBTRACTION` lines reference the station solid and rotation
  names. When the simulator switches to the sink (T-005), the yoke script has to
  take those names from the same export instead of hardcoding `RM_Station_*`.
