# Context — why this refactor, and what exists today

**Last updated:** 2026-11-05
**Design document:** [`../docs/design/generalization-plan.md`](../docs/design/generalization-plan.md) (Rev 4)
**Delivery plan:** [`plan.md`](plan.md) (Rev 4)
**Prototype:** [`../prototype/parametric_poc.py`](../prototype/parametric_poc.py)

---

## 1. What mplDTs is

`mplDTs` is a Python library that produces matplotlib representations of CMS
Drift Tube (DT) chambers and segments. It is used by `DTG4Simulator` to turn
the official CMS DT geometry into Geant4 ASCII text geometry (`.tg`), and by
analysis/plotting code to draw chambers in local or global views.

The repository contains two things that are easy to confuse:

- the **runtime model** (`mpldts/geometry/`): `Station`, `SuperLayer`, `Layer`,
  `DriftCell`, `Segment`, `AMDTSegment`;
- the **plotting layer** (`mpldts/patches/`): matplotlib patches that consume
  the model.

Only the runtime model is being generalized. The patch API must keep working.

---

## 2. Current architecture (before the refactor)

```
DTGeometry_v3.xml (20.8 MB)
        │  parsed at import time
        ▼
DTGEOMETRY  (module-level singleton, mpldts/geometry/_geometry.py:196)
        │  .get("LocalPosition", rawId=...) ...
        ▼
Station(wheel, sector, station)
  └── SuperLayer(rawId)
        └── Layer(rawId)
              └── DriftCell(number)        # really a cell, named "wire" in the XML
        │
        ├──► DTStationPatch (matplotlib)
        └──► DTG4Simulator/geometry/generate_geometry_data.py ──► .tg
```

Every class imports `DTGEOMETRY` and reads the XML in its constructor. There is
no writer, no shape abstraction, and no assembly/world object.

`TransformManager` (`mpldts/geometry/transforms.py`) stores a graph of named
frames per object. `Station` owns the CMS frames and the virtual plotting
frames (`StationNvPhi`, `StationNvEta`, `SectorRef`, `SL13Center`); `Layer`
and `DriftCell` build their own copies and copy selected matrices from their
parents.

---

## 3. Why generalize

The original goal is to build **different DT geometries for Geant4** — test
beams, telescopes, modified CMS chambers, arbitrary layer/super-layer counts,
custom sizes and positions, and possibly non-box cells (tubes with a circular
face). The current model cannot express any of that: it can only reproduce
what is in `DTGeometry_v3.xml`.

The missing boundary is not "more optional arguments". It is:

> **A declarative detector description (topology + solids + poses)
> separate from the CMS XML. The XML is one source; a backend is one consumer.**

---

## 4. Findings that motivate the design

### 4.1 Correctness

**(a) SL2 transform chain is wrong by `√2 · |SL_local_x|`.**
`Layer._setup_transformer` (around `layer.py:137-143`) subtracts a
station-frame translation from an SL-frame translation; `DriftCell` inherits
the error (`drift_cell.py:87-93`). Measured errors:

| chamber | SL1/SL3 | SL2 |
|---|---|---|
| W−2 / S1 / MB2 | 0.000 cm | **2.475 cm** |
| W0 / S5 / MB3 | 0.001 cm | **0.424 cm** |
| W−2 / S2 / MB1 | 0.000 cm | **0.707 cm** |

The stored XML `GlobalPosition` is correct; the composed transform is not.
The new model uses one explicit pose per node, so frames cannot be mixed.
**Fixed in T-022**: the legacy classes are views over those poses, the table
above is history, and `test_sl2_cell_centres` guards it.

**(b) Shared-cache mutation.** `StationsCache.get(..., dt_info=...)` returned the
same `Station` and called `set_cell_attrs`, which writes on shared `DriftCell`
objects. Event A's values leaked into event B.
**Fixed in T-023**: `Station.overlay(dt_info)` shares the node tree and the
graph and owns its cell attributes; the cache returns it and never writes to
the cached station. `test_cache_overlays_isolate_cell_attributes` guards it.

**(c) Attribute-order-dependent XML parsing.** `_geometry.py` used
`element.attrib.values()` positionally, so legal XML attribute reordering
changed `bounds` or `WiresSize`.
**Fixed in T-024**: the shim reads explicit names; `test_bounds_and_wires_do_not_depend_on_attribute_order`
pins it.

**(d) `bounds` assumes a box.** `DTFrame.width/height/length` and
`local_cords_at_min` assume rectangular extents. A tube cannot be represented;
its dimensions are `(radius, length)` and its AABB is derived. The new model
separates `shape.dimensions` from `shape.aabb()`.

**(e) Frame-name divergence.** Installed 2.2.0-beta names the SL frame
`"SuperLayer"`; the checked-out branch names it `"SL{n}"`
(`super_layer.py:115`). The G4 generator asks for `"SuperLayer"`
(`generate_geometry_data.py:131`), so installing the branch breaks every SL2
station. Fix with aliases and a version pin.

### 4.2 Performance

Measured on 2026-11-06. The checkout indexes the XML; the installed 2.2.0-beta
does not.

| measurement | checkout | installed |
|---|---|---|
| geometry import + XML parse/index | ~3.4 s | not measured |
| `Station(-2,1,2)` | 1.00 s | 1.25 s |
| `Station(2,14,4)` | 0.71 s | 2.26 s |
| `Station(0,1,1)` | 0.87 s | 1.66 s |
| all 250 (extrapolated) | ~3–4 min | ~7–10 min |

Per-cell `TransformManager` construction is still the main cost. The old
profile (3.75 s XPath, 2.64 s transforms) is from the pre-index code and is
retired. One pose per node + a shared frame graph + vectorized grids should get
a station below ~20 ms.

### 4.3 Conceptual

- The XML `<Wire>` is already the cell; no separate object is needed.
- `Shape` does not exist; a cell is implicitly a box.
- Per-object transform copies are both slow and ambiguous.
- The exporter knows CMS internals (`SL2` rotation, MB4, honeycomb), which is a
  symptom of missing shape/pose concepts.

---

## 5. Target model in one page

```
DetectorSpec (world)
├── structures: StructureSpec        [yoke, CSG payload]     physical
└── StationSpec                      [solid: Box air]        physical
    ├── attachments: SolidSpec       [honeycomb box]         physical
    └── SuperLayerSpec               [solid: None]           grouping
        └── LayerSpec                [solid: None]           grouping
            └── CellGrid → CellSpec  [solid: Box|Tube]       physical

Event layer (separate, per event)
└── Annotation: Segment | Track | Jet    frame + attributes
```

Concepts:

- **Node**: topology + optional solid. `solid=None` is a grouping frame.
- **Shape**: `Box`, `Tube`, extensible; `aabb()`, `volume()`, `symmetry_axis()`.
- **CellGrid**: pitch, count, stagger, first id; generates `Cell`s.
- **Pose**: one per node, `p_parent = R·p_child + t`; `world_pose` top-down.
- **FrameGraph**: shared named-frame graph; **FrameView** gives each object the
  old `transformer` API with scoped aliases and virtual frames.
- **Source**: `CMSXMLSource` (XML → specs) or `JSONSource`/Python builders.
- **Sink/backend**: `VolumeSink` receives folded placements; pyg4ometry (future),
  `.tg`, GDML or a test double implement it.

### 5.1 Physical extras

- **Honeycomb** is a passive `SolidSpec` attachment on the station (box, Al),
  computed by the CMS preset from the SL poses.
- **Yoke** is a detector `StructureSpec` (iron, station-shaped holes). The core
  stores the data; a CSG-capable backend builds it. Until then, the simulator
  keeps the current `.tg` boolean path.
- There is no separate wire object; the XML `<Wire>` is the cell entry.

### 5.2 Per-event data (no event layer)

- mplDTs does **not** own an event model (ADR-024). `DTPatternRecognition`
  builds the events (`Event` = typed bag of config-declared `Particle`
  records) and sends them as a table keyed by `(wh, sc, st, sl, l, w)`.
- The table is applied to the immutable station as an overlay
  (`Station.set_cell_attrs` / `overlay`), and the patches read it back.
- `Segment`/`AMDTSegments` stay as views over the `FrameGraph`; they are not
  detector solids and never enter `StationSpec` or the geometry exporter.

Full details, code sketches and the CMS mapping are in the design document.

---

## 6. Design principles

1. Specs are immutable, JSON-able and backend-free.
2. The model never performs I/O.
3. CMS is a source and a preset, not the core.
4. One pose convention; no implicit frame mixing.
5. Derive global positions; validate them against the XML oracle.
6. Keep the public API; use aliases and deprecation, not breaks.
7. Primitives in the core; CSG/backends outside.
8. Lazy cells, vectorized grids, no per-cell transform managers.
9. A future pyg4ometry bridge must be additive: one new module + optional extra
   (`mplDTs[g4]`).
10. Measure before/after: station build, full geometry, generator time.
11. Physical = station, cells, honeycomb, yoke. SL/layer are grouping; there
    is no separate wire object.
12. Event objects are annotations, not geometry; keep the legacy `Segment` API.

---

## 7. Downstream consumer

`DTG4Simulator/geometry/generate_geometry_data.py` currently:

- builds `Station(wheel, sector, station)`;
- reorders `bounds` for Geant4 (`:68`);
- asks for the `"SuperLayer"` frame (`:131`);
- rotates SL2 cells manually (`:148-149`);
- reconstructs the honeycomb gap from `local_cords_at_min` (`:190-193`);
- special-cases MB4 (`:181-182`).

The target is a generic spec walk with a `VolumeSink`, so the exporter has no
CMS knowledge. Do not refactor this generator until the model is stable.

---

## 8. Key paths and environment

| Path | Purpose |
|---|---|
| `mpldts/geometry/` | runtime model |
| `mpldts/patches/` | matplotlib consumers |
| `test/` | pytest suite (`test/geometry/`) |
| `docs/examples/` | documented examples, smoke-tested headless |
| `docs/design/generalization-plan.md` | full design |
| `prototype/parametric_poc.py` | executable model |
| `/home/destrada/Geant4/DTG4Simulator/` | downstream simulator |
| `/home/destrada/Geant4/DTG4Simulator/env/` | Python env with numpy/matplotlib/pytransform3d |

The source checkout and the installed package differ; always state which one a
measurement used. See `state.md` for versions and `commands.md` for the exact
commands.
