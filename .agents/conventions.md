# Conventions — geometry model, code and tests

**Last updated:** 2026-11-05
**Scope:** all new work in `mpldts/`, `test/`, `docs/` and `.agents/`.

These are not cosmetic preferences. The SL2 bug, the cache leak and the
frame-name break all came from violating one of them.

---

## 1. Coordinates and units

1. **Units: centimetres.** All spec fields, `Pose` translations, `Shape`
   dimensions and tolerances are in cm. Backends convert at their boundary
   (Geant4/pyg4ometry `lunit="cm"`; GDML `cm`).
2. **Pose convention:** a node's pose maps **child → parent**:
   `p_parent = R @ p_child + t`. The builder composes
   `world_pose = parent.world_pose @ node.pose` in that order.
3. **One pose per node.** Never store a second "local center" in another frame.
   Never subtract coordinates from different frames.
4. **Local axes for a DT layer/cell:**
   - `x` = pitch direction (cells repeat along x),
   - `y` = cell length (the XML “wire” direction),
   - `z` = drift/thickness direction (layers stack along z).
5. `Box(dx, dy, dz)` are **full extents**. For a CMS cell:
   `Box(4.2, 234.8, 1.3)`.
6. `Tube(radius, length, axis="y")` is a cylinder about `axis`; `aabb()` is
   derived, never the source of truth.
7. Rotations must be orthonormal: assert `‖R·Rᵀ − I‖ < 1e-9` in validation.
8. Handedness is right-handed, active rotation, as in the prototype's
   `Pose.matrix`. A backend that expects passive/Euler angles must convert
   (pyg4ometry: `matrix2tbxyz`).

---

## 2. Vocabulary (use these names)

| Term | Use | Do not use |
|---|---|---|
| `Cell` | the drift/gas volume and its centre; the XML `<Wire>` is a cell | a separate `Wire` object |
| `CellGrid` | repetition of cells (pitch, count, stagger, id) | `WireLayout` |
| `Annotation` | event-level object (segment, track, jet) | "geometry" for events |
| `Track` | a polyline annotation (muon path) | "segment" for a track |
| `Layer` | a plane of cells | "wire layer" |
| `SuperLayer` | a stack of layers | "SL" in prose (ok in ids/aliases) |
| `Station` / chamber | one DT chamber | "detector" for one station |
| `Shape` | a primitive solid | "geometry" for one shape |
| `Pose` | parent-relative rigid transform | "position" for a pose |
| `FrameGraph` | shared named-frame graph | "transformer" for the graph |
| `FrameView` | per-object view of the graph | "manager" |
| `VolumeSink` | exporter backend interface | "writer" in the core |
| `Source` | XML/JSON/Python → specs | "loader" in the model |

The XML `<Wire>` element is the **cell entry** (number + position); map it
once in `CMSXMLSource`, and never let the name leak into the model.

---

## 3. Specs and model

1. Specs are **immutable dataclasses**, JSON-able, with no behaviour beyond
   validation/convenience. No I/O, no plotting, no backend imports.
2. Physical extras are data: honeycomb is a `SolidSpec` attachment on the
   station; the yoke is a `StructureSpec` on the detector. CSG is never
   implemented in the core.
3. The XML `<Wire>` is the cell entry; there is no separate wire object,
   radius or material.
4. `shape=None` means a **grouping frame**; it contributes a pose, not a
   volume. Do not invent a dummy box for it.
5. Cells are generated from `CellGrid`; do not hand-materialize 60k cells
   unless needed. `Layer.cells` is lazy/cached.
6. IDs/names:
   - `frame_id` is a unique path: `/CMS/W-2/S1/MB2/SL2/L1/C7`.
   - node `name` is short and human-readable: `SL2`, `L1`, `C7`.
   - never use a raw XML `rawId` as a frame id; keep it as metadata.
7. Derived fields (`world_pose`, `center`, `bounds` for non-shapes) are always
   computed, never stored in a spec.
8. Any node can have a `material`; the core only carries the name. Material
   construction belongs to the backend.
9. Validation is explicit (`validate()`), not hidden in constructors.

---

## 4. Shapes

1. Implement `aabb()`, `volume()`, `symmetry_axis()` only. No `to_g4`, no
   pyg4ometry, no GDML strings in `Shape`.
2. `Box` is the only shape required for CMS. Keep the protocol generic; `Tube`
   is cheap and already prototyped, but do not add a shape speculatively.
3. New shapes need: a spec serialization branch, an AABB, a volume, and a
   backend mapping (documented, not implemented until the backend exists).
4. **No CSG** (`Union`, `Subtraction`, `Intersection`) in mplDTs. A future
   backend may accept a pre-built pyg4ometry solid; the yoke is the only
   expected CSG case.
5. A tube's native axis is explicit; the backend maps it to its own convention
   (Geant4 `Tubs` is along z, so y → `R_x(-90)`).

---

## 5. Frames and aliases

1. Full frame ids are unique paths; aliases are scoped to an object's view.
2. Required aliases: `Cell`, `Layer`, `SuperLayer`, `SL{n}`, `Station`,
   `CMS`, `World`.
3. `CMS`/`World` map to the root frame; for non-CMS detectors, `CMS` may be an
   alias of the world for compatibility, documented as such.
4. Virtual frames (`StationNvPhi`, `StationNvEta`, `SectorRef`, `SL13Center`)
   are registered by the CMS preset, not by the core.
5. `get_transformation` keeps the current contract: warn + `None` when no path.
   `transform` raises `ValueError` when no path.
6. `type="point"` (default) vs `type="vector"`: points get translation, vectors
   do not.
7. If an alias is ambiguous in a scope, raise a `KeyError` listing the available
   frames; do not guess.

---

## 6. Code style

1. Python ≥ 3.9 (see `pyproject.toml`); use `from __future__ import
   annotations` where needed.
2. `black` formatting (line length 100 is acceptable; match the file).
3. Type hints on public functions and dataclasses.
4. Docstrings: short summary, parameters when non-obvious, units.
5. No new mandatory dependencies. Optional extras go in `pyproject.toml` and
   must be lazily imported.
6. Never import `matplotlib`, `pandas`, `pytransform3d` or a backend from the
   core geometry modules unless already required; keep the core numpy-only.
7. No mutable default arguments; use `field(default_factory=...)`.
8. Errors: `ValueError` for invalid user data, `KeyError` for missing
   frames, `TypeError` for wrong types. Include the offending id/name.

---

## 7. Tests

1. `pytest`, tests under `test/geometry/`.
2. Every geometry change needs:
   - a unit test for the new ref;
   - the CMS oracle (computed centres vs XML `GlobalPosition`);
   - the transform invariant (`Cell → CMS`);
   - a JSON round-trip when serialization is touched.
   - a `RecordingSink`/placement test when the exporter seam is touched.
   - event-layer changes need transform, collection and JSON tests, and must
     assert that nothing enters the detector spec/exporter.
3. Tolerances:
   - positions: `1e-6` cm for node fields, `2e-3` cm for the cell-centre
     oracle (the XML stores 3 decimals, so 1e-3 sits at the rounding floor);
   - rotations: `1e-9` for orthonormality, `1e-6` for round-trips.
4. Never loosen a tolerance without an ADR; never delete `xfail(BUG-01)` —
   remove the marker only when the fix is in.
5. No network, no GUI, no sleeps in tests. Visual scripts are not tests and
   do not live in `test/`: T-025 converts, moves or deletes them.
6. Performance budget (non-blocking CI): one station `< 50 ms` in Phase 1,
   `< 20 ms` in Phase 2; full CMS `< 10 s`.
7. Tests must be deterministic; seed any random rotation test.

---

## 8. Compatibility and deprecation

1. Keep `Station(wheel=..., sector=..., station=...)`, `SuperLayer(rawId=...)`,
   `Layer(rawId=...)`, `DriftCell(number=...)` working until 3.0.
2. Keep `obj.transformer` working as a `FrameView` with the same methods.
3. Keep the plotting API (`faceview`, `local`, `inverted`, `vmap`, patch
   constructors) working; use defaults/aliases, not breaks.
4. Deprecations: `DeprecationWarning`, a documented alternative, and a removal
   target (3.0).
5. Frame-name aliases (`"SuperLayer"`, `"SL{n}"`) must both resolve; this is a
   bug fix, not a compatibility hack.
6. Never change the XML file; it is the oracle.

---

## 9. Git and review

1. Branch: `feature/T-0xx-<slug>` from `main` (e.g.
   `feature/T-003-cms-oracle`).
2. Commit message: `T-0xx: <imperative summary>` (e.g.
   `T-003: add CMS oracle test`).
3. One ticket = one branch = one PR; one logical change per commit. Do not mix
   refactor and behaviour change.
4. The maintainer merges; the agent does not merge its own PR.
4. Run `pytest` before committing; if a test is red, say so in the message.
5. Do not force-push shared branches. Do not commit generated `.tg`/GDML,
   `env/`, `__pycache__/`, or secrets.
6. Update `state.md`/`TICKETS.md`/`PROGRESS.md` in the same commit as the code when practical.

---

## 10. Documentation and `.agents`

1. The design document is the technical source of truth; update it when the
   model/API changes.
2. `.agents/state.md` is updated every session; `.agents/TICKETS.md` and
   `.agents/PROGRESS.md` when a ticket changes state.
3. Any non-obvious choice gets an ADR in `.agents/decisions.md` using
   `templates/adr.md`.
4. Keep docs in English, with units and frame names explicit.
5. Do not duplicate long design text in `.agents`; link to the design document.
---

## 11. Physical volumes and event objects

### Physical volumes

| Object | Physical | Representation |
|---|---|---|
| Station (air) | yes | `StationSpec.shape`, `material="G4_AIR"` |
| Cell (gas) | yes | `CellGrid`/`CellSpec.shape`, gas material |
| Honeycomb (Al) | yes | `StationSpec.attachments` (`SolidSpec`) |
| Yoke (Fe, holes) | yes | `DetectorSpec.structures` (`StructureSpec` + subtractions) |
| Super layer / layer | no | grouping frames (`shape=None`) |

- The honeycomb is computed by the CMS preset from SL poses; the core sees a
  passive solid.
- The yoke's CSG is a backend concern. A backend that cannot do CSG rejects it
  explicitly; the simulator keeps the current `.tg` boolean path until then.
- `VolumeSink` must receive station, cell, attachment and structure
  placements; there is no wire object to emit.

### Event objects

- Segments, tracks and jets are **annotations**, not detector solids. They
  live in `mpldts/events/` (Phase 4), reuse the `FrameGraph`, and never enter
  `StationSpec` or the geometry exporter.
- `Segment`: endpoints or centre + direction + length.
- `Track`: ordered polyline + per-point attributes.
- `Jet`/`Cone`: apex + axis + half-angle + attributes.
- Attributes are an opaque bag; do not build a full event data model.
- Keep the current `Segment`/`AMDTSegment` API working (compatibility).
