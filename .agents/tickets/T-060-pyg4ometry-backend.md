# T-060 — pyg4ometry backend + GDML (deferred)

- **Status:** deferred
- **Phase:** 6
- **Epic:** E6 Future backend
- **Depends on:** T-052 (and all phases 0–5 merged)
- **Branch:** `feature/T-060-pyg4ometry-backend`
- **PR:** —
- **Owner:** unassigned
- **Labels:** future, pyg4ometry, gdml

## Context

pyg4ometry is the natural backend for GDML and future solids, but it is a heavy
optional dependency and is intentionally deferred. The compatibility contract
is in [`../pyg4ometry-readiness.md`](../pyg4ometry-readiness.md) and design doc
§8.0.

## Scope (when started)

- Add `mpldts/export/base.py` (`VolumeSink`, `VolumePlacement`) and
  `recording.py` (test sink) — if not already in the library.
- Add `mpldts/export/pyg4ometry.py` as an optional extra (`mplDTs[g4]`):
  - `PyG4ometrySink(VolumeSink)`: `Box`/`Tubs`, `LogicalVolume`,
    `PhysicalVolume`, `matrix2tbxyz`, materials;
  - `to_pyg4ometry(...)` convenience wrapper;
  - `AssemblyVolume` or folded poses for grouping nodes.
- GDML writer and `G4GDMLParser` integration in `DTG4Simulator`.
- Tests: rotation round-trip, AABB, cell centres, overlap check, GDML load.
- Keep `.tg` working; do not remove it in the same PR.

## Out of scope

- Making pyg4ometry a mandatory dependency.
- CSG in the core; only the backend may use booleans.
- Changing the detector specs (they are already backend-neutral).

## Entry criteria

- [ ] Phases 0–5 merged.
- [ ] `VolumeSink` seam exists in the library and is tested.
- [ ] ADR-008/ADR-014 revisited and accepted for implementation.
- [ ] Output decision recorded (GDML first; `.tg` kept for the yoke).
- [ ] The optional extra name (`mplDTs[g4]`) is agreed.

## Acceptance criteria (when started)

- [ ] `mpldts.geometry` does not import pyg4ometry.
- [ ] Box and tube stations export.
- [ ] `tbxyz2matrix(matrix2tbxyz(R)) == R` for random rotations.
- [ ] Every solid AABB matches `shape.aabb()`.
- [ ] `checkOverlaps(recursive=True)` reports zero overlaps on a small station.
- [ ] GDML loads in Geant4 (or the pyg4ometry reader).
- [ ] `.tg` path still passes its parity test.

## Verification (future)

```bash
pip install pyg4ometry
pytest -q test/geometry/test_pyg4ometry_export.py
```

## Risks / notes

- pyg4ometry pulls VTK/CGAL; keep it out of the core and CI default job.
- Do not reopen the model design to accommodate the backend; if something is
  missing, add it additively or file a new ticket.

## Progress

- 2026-11-05: deferred by ADR-008/ADR-014.
