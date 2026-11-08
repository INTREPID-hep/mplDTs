# T-031 — CMS preset remainder and custom-station plotting

- **Status:** done
- **Phase:** 3
- **Epic:** E3 Assemblies and extras
- **Depends on:** T-030 (done)
- **Branch:** `feature/phase-3-assemblies`
- **PR:** — (branch pushed; the maintainer merges)
- **Owner:** —
- **Labels:** model, plotting, cms
- **Completed:** 2026-11-08

## Context

T-030 delivered the generic half: `_add_natural_views` registers
`StationNvPhi` and `StationNvEta` for a CMS chamber and for a station built
from a spec, and the patches choose the super layers of the phi and eta views by
orientation (`dt_station_patch._is_turned`) instead of
`super_layer.number == 2`.

Still CMS-only and welded to the CMS constructor: `SectorRef` (the sector phi
line, with the MB4 sectors 13/14 sign correction) and `SL13Center` (the
geometrical centre of the super layers 1 and 3), plus the face factor of the
natural views, which a station built from a spec could only guess.

## What was delivered

- New package `mpldts/geometry/presets/` and `presets/cms.py` with
  `face_factor(wheel, sector)` and `add_frames(graph, node, record, wheel, sector)`
  (`SectorRef` + `SL13Center`). The module reads the record and the node
  poses, imports no plotting and no XML parser, and reuses the source's
  `NEGATIVE_FACE_SECTORS`.
- `station.py` lost `_face_factor` and `_add_plotting_frames`; `_built`
  registers the natural views and then `cms.add_frames`.
  `Station.face_orientation_factor` now asks the preset, same values.
- `_face_from_pose(node)`: the face factor of any station from its pose
  (the z component of its length axis). `Station.from_spec` uses it, so a
  mirrored custom chamber inverts its views the right way.
- `test/geometry/test_presets.py`: the natural views of the representative
  chambers follow `face_factor`, a custom station has the natural views and no
  CMS frames, a mirrored station inverts, and a slow sweep checks all 250
  chambers.

## Out of scope

- Rewriting the patch layer or its artist structure.
- Image comparison tests.
- Any change to the spec or node-tree levels.

## Acceptance criteria

- [x] `StationNvPhi`, `StationNvEta`, `SectorRef` and `SL13Center`
      resolve exactly as before for all 250 CMS chambers (slow sweep).
- [x] A station built from a spec has the natural views and no `SectorRef` or
      `SL13Center`.
- [x] CMS patch rectangles are unchanged: 60 collections (5 chambers x 2 views x 3
      local/inverted modes) against the `v2.3.0` tag, worst vertex deviation
      **0.0** in display coordinates, transforms included.
- [x] A mirrored custom station inverts its local view correctly.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q          # 143 passed, 2 skipped
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow  # 3 passed (250 chambers)
```

The Sphinx build is warning-free and documents `mpldts.geometry.presets.cms`.

## Risks / notes

- The face factor is now derived from the pose for every station, including the
  CMS ones; `test_the_face_factor_matches_the_pose_on_every_chamber` pins
  that it equals the wheel/sector rule on all 250 chambers.
- The preset imports `NEGATIVE_FACE_SECTORS` from the source (preset -> source
  -> specs), so the CMS naming rule lives in one place.
- `Station.face_orientation_factor` for a station built from a spec still
  reports the CMS formula on wheel/sector 0; the views use the pose.
