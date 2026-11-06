# Decisions — ADR log

**Last updated:** 2026-11-05
**Format:** see [`templates/adr.md`](templates/adr.md).
**Rule:** an accepted ADR is not reopened silently. Propose a new ADR that
supersedes it, with the reason.

---

## ADR-001 — Declarative specs, sources and a builder

**Status:** accepted · 2026-11-05
**Context:** every geometry class reads the CMS XML singleton directly; custom
geometries are impossible without editing the XML.
**Decision:** introduce immutable specs (`StationSpec`, ...), sources
(`CMSXMLSource`, JSON/Python) and a builder (`build_station`). The model
classes consume specs and never perform I/O.
**Consequences:** one extra layer, but the XML becomes replaceable. The public
constructors become compatibility wrappers. The spec is the single source of
truth for plotting/export.

---

## ADR-002 — One pose per node, child → parent, centimetres

**Status:** accepted · 2026-11-05
**Context:** the current code mixes station-frame and SL-frame coordinates,
which causes the SL2 error; `local_center` semantics are inconsistent.
**Decision:** every node stores exactly one parent-relative pose
`p_parent = R·p_child + t`; global poses are derived top-down; all lengths are
cm; local axes are x=pitch, y=cell length, z=drift.
**Consequences:** removes a class of frame-mixing bugs; exporters are simple
pose walks. Sizes are full extents, not half-lengths.

---

## ADR-003 — Cell and CellGrid; XML `<Wire>` is the cell entry

**Status:** accepted · 2026-11-05 · **amended by ADR-019**
**Context:** `DriftCell` is addressed by `wireNumber`, and the XML `<Wire>`
elements were treated as wires. The XML element is actually the cell entry.
**Decision:** model a `Cell` (shape) and a `CellGrid` (pitch/count/stagger/
first id). The CMS source maps `<Wire>` → cell entry once. There is no
separate `Wire` object.
**Consequences:** naming is unambiguous; no extra object or solid is exported.
The old `DriftCell` remains as a compatibility alias for a cell.

---

## ADR-004 — Primitive shapes in the core; CSG out of scope

**Status:** accepted · 2026-11-05
**Context:** revision 1 assumed boxes. Tube cells (circular face) are required,
and other primitives may follow.
**Decision:** `Shape` with `aabb()`, `volume()`, `symmetry_axis()`; implement
`Box` and `Tube`; add more primitives as needed. Do not implement CSG; a future
backend can accept a pre-built pyg4ometry solid.
**Consequences:** no CAD kernel in mplDTs; tubes work; the shape API stays
small. Exotic solids are a backend concern.

---

## ADR-005 — Shared `FrameGraph`, per-object `FrameView`

**Status:** accepted · 2026-11-05
**Context:** each object builds a private `TransformManager` and copies
sub-chains; names are ambiguous (`Layer`, `Cell`) and copies go stale.
**Decision:** one shared graph per detector; unique path frame ids; scoped
aliases in a `FrameView` returned by `obj.transformer`; virtual frames are
graph edges. Keep `get_transformation`, `transform`, `available_frames`,
`add`/`remove` and `__str__` working.
**Consequences:** backward-compatible queries; no stale copies; one edge per
node. Global poses are still computed top-down in the builder, not by BFS.

---

## ADR-006 — CMS is a source and a preset, not the core

**Status:** accepted · 2026-11-05
**Context:** wheel/sector ranges, face orientation, sector-φ, MB4 13/14, SL13
and the SL2 rotation are baked into `Station`/`SuperLayer`.
**Decision:** move CMS semantics to `sources/cms_xml.py` and
`presets/cms.py`; the core knows only nodes, shapes, poses and frames.
**Consequences:** custom detectors do not inherit CMS rules; CMS behaviour is
preserved by the preset and the oracle. Plotting needs an orientation-based
phi/eta choice (Phase 3).

---

## ADR-007 — Immutable geometry, per-event data overlay

**Status:** accepted · 2026-11-05
**Context:** `StationsCache` returns a shared mutable `Station` and
`set_cell_attrs` writes on shared cells; event data leaks.
**Decision:** geometry is immutable after build; per-event values (time,
charge, ...) live in an overlay keyed by `(sl, layer, cell)` or are attached to
a cloned view, never to the cached geometry.
**Consequences:** fixes `BUG-02`; the cache holds specs/read-only objects;
plotting passes event data explicitly.

---

## ADR-008 — pyg4ometry deferred; `VolumeSink` seam now

**Status:** accepted (deferred; amended by ADR-014) · 2026-11-05
**Context:** pyg4ometry is a natural Geant4 backend, but adding it now would
pull VTK/CGAL into the critical path and delay the model refactor.
**Decision:** do not implement or depend on pyg4ometry in phases 0–5. The
backend-agnostic seam (`VolumeSink`, `iter_volume_placements`, backend-neutral
`Shape`, 4×4 `Pose.matrix`, stable specs, `mpldts/export/`) is implemented
with the first exporter (`TgSink`) in Phase 5, not before. A future
`PyG4ometrySink` must be additive.
**Consequences:** no dependency now; the bridge can be a new module later. A
`RecordingSink` test proves the seam when the first sink exists. Phase 6 is
explicitly deferred until phases 0–5 are merged and this ADR is revisited. The
future contract is in [`pyg4ometry-readiness.md`](pyg4ometry-readiness.md).

---

## ADR-009 — The CMS XML globals are the oracle

**Status:** accepted · 2026-11-05
**Context:** the model must reproduce CMS; the XML contains a `GlobalPosition`
for every cell, which is independent of the new pose code.
**Decision:** for every chamber, rebuild cell centres from specs and assert
`|computed − XML| < 1e-3 cm`. Keep the XML values as
`metadata["reference"]`; never use them in the model.
**Consequences:** catches SL2 and future pose regressions; makes the refactor
provably behaviour-preserving. If the oracle fails, fix the source, not the
tolerance.

---

## ADR-010 — Backward compatibility until 3.0

**Status:** accepted · 2026-11-05
**Context:** `DTG4Simulator`, the plotting layer and user scripts depend on the
current constructors, the `transformer` API and frame names.
**Decision:** keep `Station(wheel, sector, station)`, `rawId` constructors,
`obj.transformer`, `get_transformation`/`transform`/`available_frames` and the
plotting API working. Use aliases and deprecation warnings; remove in 3.0.
**Consequences:** more shim code, but no forced downstream rewrite. Every shim
has a removal target and a test.

---

## ADR-011 — Physical volume policy

**Status:** accepted · 2026-11-05
**Context:** the maintainer confirmed which objects are physical in the
simulation and which are logical grouping.
**Decision:** physical: station (air), drift cells (gas), honeycomb
(aluminium), yoke (iron). Non-physical: super layers and layers (grouping
frames). There is no separate wire object. The core carries the data;
exporters decide how to build it.
**Consequences:** a shallow G4 hierarchy (station → cells), plus attachments
and structures. SL/layer never become volumes unless a future detector
explicitly gives them a shape. The yoke needs CSG, which is a backend concern.

---

## ADR-012 — Cell and wire are the same object

**Status:** accepted · 2026-11-05 · **amended by ADR-019**
**Context:** the XML `<Wire>` element is the cell entry (number + position).
Revision 2 invented a separate wire entity; that was unnecessary.
**Decision:** use `Cell` only. The XML `<Wire>` maps to the cell; there is no
`Wire` object, radius, material or volume. Analysis/segments use
the cell centre when they need the line.
**Consequences:** one object instead of three; the geometry stays simple. If a
physical anode is ever needed, it is a new shape/solid with an explicit ADR.

---

## ADR-013 — Box first, generic `Shape` protocol

**Status:** accepted · 2026-11-05
**Context:** only box cells are needed for CMS now, but the model should not
preclude tubes or future primitives.
**Decision:** keep the `Shape` protocol (`aabb`, `volume`, `symmetry_axis`) and
implement `Box` first. `Tube` is cheap and already prototyped; add other
primitives only when a detector needs them. No CAD kernel.
**Consequences:** generic without speculative complexity. A backend maps
shapes to its solids; exotic shapes can be added later.

---

## ADR-014 — pyg4ometry is an optional extra

**Status:** accepted · 2026-11-05 (amends ADR-008)
**Context:** the maintainer prefers pyg4ometry as an extra of mplDTs rather
than a separate package; it remains deferred.
**Decision:** when Phase 6 starts, `pyg4ometry` is an optional extra
(`mplDTs[g4]`), lazily imported. `mpldts.geometry` never imports it. The
backend lives in `mpldts/export/pyg4ometry.py` and implements `VolumeSink`.
**Consequences:** no core dependency, no CI default install; the readiness
contract in `pyg4ometry-readiness.md` applies.

---

## ADR-015 — `.tg` first, GDML later

**Status:** accepted · 2026-11-05
**Context:** the simulator already reads `.tg`; GDML is the cleaner long-term
format, but it requires a backend.
**Decision:** implement `TgSink(VolumeSink)` in Phase 5 and prove parity with
the current generator. Add GDML through the optional pyg4ometry backend in
Phase 6. Both consume the same placements.
**Consequences:** no output-format rewrite in the critical path; GDML remains
additive. The yoke's `.tg` boolean path stays in the simulator until a CSG
backend exists.

---

## ADR-016 — Event objects are a separate annotation layer

**Status:** accepted · 2026-11-05
**Context:** `Segment`/`AMDTSegment` exist; the maintainer asks whether tracks
and jets/cones can be extensions.
**Decision:** add `mpldts/events/` as an annotation layer: `Annotation`,
`Segment`, `Track` (polyline), `Jet`/`Cone`, collections, plotting adapters.
They reuse the `FrameGraph`, keep attributes as an opaque bag, and never enter
the detector spec or geometry exporter. The current `Segment` API stays
compatible. Phase 4.
**Consequences:** segments/tracks/jets share transforms and plotting without
polluting the geometry. Scope is deliberately small (three types, no full
event model). Jets are visual objects, not solids.

---

## ADR-017 — Honeycomb and yoke are data, CSG is a backend concern

**Status:** accepted · 2026-11-05
**Context:** honeycomb is a passive box; the yoke is iron with station-shaped
holes. Implementing CSG in mplDTs would turn it into a CAD kernel.
**Decision:** honeycomb is a `StationSpec.attachments` `SolidSpec` (shape,
pose, material), computed by the CMS preset from SL poses. The yoke is a
`DetectorSpec.structures` `StructureSpec` (shape, subtractions, material);
the core stores the data, a CSG-capable backend builds it. Until then, the
simulator keeps the current `.tg` boolean path. A backend without CSG rejects
the structure explicitly.
**Consequences:** the data model is ready for pyg4ometry/GDML without a
dependency now; the yoke is not blocked by the geometry refactor.

---

## ADR-018 — Plan revision 4: specs first, optional events, first-exporter seam

**Status:** accepted · 2026-11-06
**Context:** plan Rev 3 made Phase 1 a half-refactor without specs, duplicated
the CMS work across Phases 2/3, put the oracle in Phase 0 before specs existed,
built `VolumeSink` before any exporter, and planned a CLI/YAML nobody asked
for. It also carried stale performance numbers.
**Decision:** the delivery order is specs + CMS source (Phase 1) → runtime
model + compatibility (Phase 2) → assemblies/extras, optional events, authoring
in parallel. `VolumeSink` is introduced with `TgSink` in Phase 5. CLI and YAML
are out of scope. Event annotations are optional and off the critical path.
`BUG-01` is fixed in Phase 2 when the runtime model is replaced. Baselines are
the 2026-11-06 measurements on the checkout.
**Consequences:** one model rewrite instead of two; the oracle validates the
spec path before the runtime changes; fewer speculative modules. The technical
design is unchanged; this ADR governs ordering and scope. It amends the phase
numbering in ADR-008/ADR-014.

---

## ADR-019 — The XML `<Wire>` is the cell; no separate wire object

**Status:** accepted · 2026-11-06
**Context:** the design carried a separate `Wire` concept in
several places. The maintainer clarified that a DT cell and its XML `<Wire>`
entry are the same thing; the XML element only gives the cell coordinates.
**Decision:** delete the separate wire entity from the model, specs, JSON,
tests and docs. A `Cell` is the gas/drift volume and its centre; `CellGrid` repeats
cells. The CMS source maps `<Wire>` → `Cell` once. No wire solid is ever
exported.
**Consequences:** simpler model and serialization; no duplicate concept. The
XML names `<Wire>`, `WiresSize`, `WiresRange`, `wireNumber` stay only inside
`sources/cms_xml.py` as historical XML vocabulary.

---

## Decisions from the maintainer (2026-11-05)

| Question | Answer | ADR |
|---|---|---|
| Physical volumes | station, cells, honeycomb, yoke; SL/layer grouping | ADR-011 |
| Shapes | Box now; generic protocol; Tube optional | ADR-013 |
| Wire / cell | the XML `<Wire>` is the cell; no separate object | ADR-019 |
| pyg4ometry | optional extra `mplDTs[g4]`, deferred | ADR-014 |
| Output | `.tg` first, GDML later | ADR-015 |
| Event objects | separate annotation layer; segments/tracks/jets | ADR-016 |
| Honeycomb/yoke | data; CSG in a backend | ADR-017 |

## Open decisions

None blocking the plan. The defaults were resolved in Rev 4 and recorded in
`TICKETS.md` §7 / ADR-018:

| Id | Question | Resolution |
|---|---|---|
| O-01 | Compatibility horizon? | until 3.0 |
| O-02 | Plotting: orientation-based phi/eta? | yes, keep `faceview` |
| O-03 | Event scope? | Segment/Track/Jet only; no hits/digis |
| O-04 | Yoke: keep in simulator or a `.tg` CSG sink? | keep in simulator until Phase 6 |
| O-05 | Phase 0 granularity? | six tickets; T-004 folded into T-003 |

Changing a resolution requires a new ADR.
