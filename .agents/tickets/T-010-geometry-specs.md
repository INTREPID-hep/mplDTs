# T-010 — Geometry specs

- **Status:** done
- **Phase:** 1
- **Epic:** E1 Specs + source
- **Depends on:** T-003
- **Branch:** `feature/T-010-geometry-specs`
- **PR:** —
- **Owner:** unassigned
- **Labels:** architecture, specs

## Context

Revision 3 tried to introduce a `GeometrySource` protocol before the spec
types existed, then rewrote the model classes in Phase 2. That was a
half-refactor. This ticket starts with the data layer only: the immutable,
JSON-able description the source and builder will share.

The runtime classes (`Station`, `SuperLayer`, `Layer`, `DriftCell`) are
untouched by this ticket.

## Scope

- Add `mpldts/geometry/specs.py`:
  - `Pose` (parent-relative rotation + translation, `compose`, `inverse`,
    `matrix`, point/vector transform); units cm.
  - `Shape` with `aabb()`, `volume()`, `symmetry_axis()`; `Box`, `Tube`.
  - `CellGrid` (pitch, count, shape, first_id, offset) and
    `x_positions()`.
  - `LayerSpec`, `SuperLayerSpec`, `StationSpec`, `DetectorSpec`;
    optional `attachments`/`structures` fields may be added later, but do not
    implement CSG.
  - `validate(spec)` for positive sizes, orthonormal rotations, cell fit.
- Add unit tests: pose composition/inverse, box/tube AABB and volume, grid
  stagger/first id, validation errors.
- Keep the module free of XML, ElementTree, matplotlib and backend imports.

## Out of scope

- `CMSXMLSource` (T-011).
- The oracle (T-012).
- Runtime `Node`/builder/FrameGraph (Phase 2).
- JSON serialization (T-051).
- CSG, materials construction, plotting.

## Acceptance criteria

- [x] Specs are immutable dataclasses with no I/O and no backend import.
- [x] `Pose` round-trips: compose/inverse within `1e-9`.
- [x] `Box` and `Tube` AABB/volume are correct; a tube axis is explicit.
- [x] `CellGrid` reproduces the CMS 49/50/49/48 pattern and half-cell stagger.
- [x] `validate` rejects negative sizes, non-orthonormal rotations and cells
      wider than their layer.
- [x] There is no separate wire object; the XML `<Wire>` maps to a cell.

## Verification

```bash
cd /home/destrada/mplDTs
source /home/destrada/Geant4/DTG4Simulator/env/bin/activate
PYTHONPATH=/home/destrada/mplDTs pytest -q test/geometry/test_specs.py
```

## Risks / notes

- Do not add a separate `Wire` object; the XML `<Wire>` is the cell entry
  (ADR-019).
- Do not overfit the spec to CMS: no wheel/sector/station fields in the core.
- Keep `Shape` small; add primitives only when a detector needs them.

## Progress

- 2026-11-05: proposed as a `GeometrySource` protocol (too early).
- 2026-11-06: rewritten as the specs ticket; the source is T-011.
- 2026-11-06: done. `specs.py` with Pose/Shape/Box/Tube/CellGrid and the four
  node specs; `validate()` checks poses, shapes and the cell fit.
  22 tests in `test/geometry/test_specs.py`.
