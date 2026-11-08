# pyg4ometry readiness — the contract for a future backend

**Status:** deferred (ADR-008). Do not implement now.
**Purpose:** guarantee that adding pyg4ometry later is a new module, not a
refactor of the model.

---

## 1. Invariants that must stay true

1. **No backend import in the core.** `mpldts/geometry/` must not import
   `pyg4ometry`, `geant4`, `vtk`, `pytransform3d` (except where already used for
   math), or read GDML.
2. **`Shape` is backend-neutral.** It exposes `aabb()`, `volume()`,
   `symmetry_axis()` only. It does not know about `Tubs`, `Box`, or Geant4 units.
3. **The exporter seam is `VolumeSink`.** The core produces
   `VolumePlacement(node, mother, pose_in_mother)`; a backend implements
   `begin` / `place` / `end`.
4. **Grouping nodes are folded.** A node with `shape=None` contributes a pose,
   not a volume. The backend never has to invent a dummy solid.
5. **Poses are 4×4 homogeneous transforms.** `Pose.matrix` is the only
   conversion point; rotation/Euler conversion happens in the backend.
6. **Physical policy is explicit.** Station, cells, honeycomb and yoke are
   solids; SL/layer are grouping; there is no separate wire object. A backend
   that cannot do CSG may reject the yoke structure explicitly.
7. **Specs are the only input.** `StationSpec`/`DetectorSpec` + JSON schema
   contain shape, material and pose. The backend reads specs (or the built
   tree), never the XML.
8. **No CSG in mplDTs.** If a future geometry needs booleans, the backend
   accepts a pre-built pyg4ometry solid; the core stays primitive-only.
9. **Optional dependency.** `pyg4ometry` is an extra (`mplDTs[g4]`), lazily
   imported, with a clear error if missing.
10. **Public API unchanged.** `Station(...)`, `obj.transformer`, plotting and
   frame aliases keep working.

---

## 2. What already exists

| Piece | Where | Status |
|---|---|---|
| `VolumeSink` protocol | prototype §6; design doc §8.0 | done |
| `RecordingSink` | prototype §6 | done |
| `iter_volume_placements` (folding) | prototype §6 | done |
| `Shape` + `symmetry_axis` | prototype §2 | done |
| `g4_alignment` adapter (z→y) | prototype §6 | done |
| `AttachmentSpec` / `StructureSpec` hook | design doc §14 | done (T-032, T-033) |
| `.tg` sink (`TgSink`) | design doc §16; T-052 | done (2.5.0, parity with the generator) |
| 4×4 `Pose.matrix` | prototype §1 | done |
| JSON with shape/material | prototype §7; `mpldts/geometry/serialize.py` | done (T-051) |
| CMS 49/50/49/48 + stagger | prototype §8 | done |

The library has the seam (`mpldts/export/base.py`), the recording sink and
the `.tg` backend. What is missing is only the pyg4ometry sink (T-060) and the
GDML writer, both behind the optional `mplDTs[g4]` extra.

---

## 3. What a future implementation must provide

```
mpldts/export/
  base.py           # VolumeSink, VolumePlacement (no backend import)
  recording.py      # RecordingSink (tests)
  pyg4ometry.py     # optional; imports pyg4ometry lazily
```

`mpldts/export/pyg4ometry.py`:

- `PyG4ometrySink(VolumeSink)`:
  - `begin(root)`: create `g4.Registry`, world logical volume;
  - `place(node, mother, pose)`: create/reuse the solid, `LogicalVolume`,
    `PhysicalVolume`; convert `pose.matrix[:3,:3]` with
    `transformation.matrix2tbxyz`, position in cm;
  - `end()`: `registry.setWorld(...)`.
- `to_pyg4ometry(detector_or_station, materials=None, lunit="cm")` convenience
  wrapper.
- Pass station, cell, honeycomb (`SolidSpec`) and yoke (`StructureSpec`)
  placements. For the yoke, use pyg4ometry booleans in the backend.
- Material map: node material name → `MaterialPredefined`/compound; do not
  build materials in the core.
- Grouping nodes: they are already folded by the planner. If preserving the
  hierarchy matters, use `AssemblyVolume` instead of folding, but keep the
  `VolumeSink` contract.

---

## 4. Validation checklist for the future PR

- [ ] `transformation.tbxyz2matrix(matrix2tbxyz(R)) == R` (random rotations,
      1e-9).
- [ ] Every solid AABB matches `shape.aabb()` (1e-6 cm).
- [ ] Every built cell centre matches the spec (1e-9 cm).
- [ ] `logical_volume.checkOverlaps(recursive=True)` reports zero overlaps on
      a small station.
- [ ] GDML is written and loaded back (pyg4ometry reader or `G4GDMLParser`).
- [ ] Box and tube stations both export.
- [ ] `pyg4ometry` is an optional extra (`mplDTs[g4]`); importing
      `mpldts.geometry` does not import it.
- [ ] Honeycomb is exported; the yoke is either built with booleans or
      rejected with a clear error.
- [ ] The CMS `.tg` path still works (or is retired with an ADR).

---

## 5. Entry criteria

1. Phases 0–5 are merged.
2. The `VolumeSink` seam exists in the library and is tested with
   `RecordingSink`.
3. ADR-008 is revisited and accepted for implementation.
4. The output decision is recorded (ADR-015: `.tg` first, GDML later).

---

## 6. Anti-patterns (reject these)

- `Shape.to_g4()` or `Shape.to_gdml()` in the core.
- A separate `Wire` object or solid.
- Importing pyg4ometry in `mpldts/geometry/`.
- A `TransformManager` per cell again.
- Passing `bounds` tuples with implicit axis order to the backend.
- Assuming every cell is a box.
- Generating GDML strings by hand in the model.
- Making pyg4ometry a mandatory dependency.
