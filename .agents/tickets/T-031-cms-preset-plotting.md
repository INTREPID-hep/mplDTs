# T-031 — CMS preset remainder and custom-station plotting

- **Status:** ready
- **Phase:** 3
- **Epic:** E3 Assemblies and extras
- **Depends on:** T-030 (done)
- **Branch:** `feature/phase-3-assemblies`
- **PR:** —
- **Owner:** unassigned
- **Labels:** model, plotting, cms

## Context

T-030 delivered the generic half: `_add_natural_views` registers
`StationNvPhi` and `StationNvEta` for a CMS chamber and for a station built
from a spec, and the patches choose the super layers of the phi and eta views by
orientation (`dt_station_patch._is_turned`) instead of
`super_layer.number == 2`.

Still CMS-only and welded to the CMS constructor: `SectorRef` (the sector phi
line, with the MB4 sectors 13/14 sign correction) and `SL13Center` (the
geometrical centre of the super layers 1 and 3). They live in
`station._add_plotting_frames`, which only the CMS path calls, so the frames
are correct today but the CMS knowledge has no home. A station built from a spec
gets the natural views with a face factor of 1.0 because there is no wheel and
sector to derive it from.

## Scope

- Move `SectorRef` and `SL13Center` out of `station.py` into a CMS preset
  (a small function next to `mpldts/geometry/sources/cms_xml.py`) applied by
  `_built` only; the generic path keeps `_add_natural_views`.
- Derive the face factor of a station built from a spec from its pose (the sign
  that makes the natural views look at the chamber front) instead of the
  constant `1.0`; a CMS chamber keeps `_face_factor(wheel, sector)`.
- Keep `faceview=` and the segment convention (`seg.sl == 2`) working;
  document the segment rule as a rule of the segments, not of the station.

## Out of scope

- Rewriting the patch layer or its artist structure.
- Image comparison tests.
- Any change to the spec or node-tree levels.

## Acceptance criteria

- [ ] `StationNvPhi`, `StationNvEta`, `SectorRef` and `SL13Center`
      resolve exactly as before for all 250 CMS chambers (slow sweep).
- [ ] A station built from a spec has the natural views and no `SectorRef` or
      `SL13Center`.
- [ ] CMS patch rectangles are unchanged (compare `DTStationPatch` output on
      several chambers before and after).
- [ ] A mirrored custom station inverts its local view correctly.

## Verification

```bash
cd /home/destrada/mplDTs
PYTHONPATH=/home/destrada/mplDTs pytest -q
PYTHONPATH=/home/destrada/mplDTs pytest -q -m slow
```

## Risks / notes

- A wrong orientation rule is invisible in a smoke test; keep the
  `_is_turned` equivalence test and compare rectangles, not just path counts.
- The face factor of a custom chamber can only be guessed from its pose; record
  the rule in the docstring and pin it with a mirrored station test.
