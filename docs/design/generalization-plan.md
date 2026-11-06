# Generalizing mplDTs: topology, solids, cells, frames — and a pyg4ometry bridge

**Status:** revision 4 — **approved 2026-11-06; Phase 0 (safety net) in progress**
**Supersedes:** revision 3 and `generalization-plan-v1.md` (the v1 file was removed in Rev 4)
**Scope:** `mplDTs` geometry layer and its interface with `DTG4Simulator`
**Companion artefact:** `prototype/parametric_poc.py` (runnable, numpy-only)

Revision 2 fixed three mistakes in revision 1; revision 3 adds the maintainer decisions, the physical/event layers and the ticket workflow:

1. **Cell = XML `<Wire>`; there is no separate wire object.** A drift cell is
   the gas/drift volume and its centre. The XML `<Wire>` elements are the
   **cell entries** (number + local/global position); revision 1 called the
   repetition a `WireLayout`, which was the naming confusion. The model keeps
   `Cell`, `CellGrid` and `Shape`; it does not need a separate wire
   object.
2. **Not only boxes.** A cell can be a cylinder/tube (circular cross-section),
   a trapezoid, or another primitive. Revision 1's "DT-like boxes" is replaced
   by a small `Shape` protocol (Box, Tube, extensible), with CSG deliberately
   delegated to pyg4ometry.
3. **Transformations were under-specified.** The current `transformer` is a
   named-frame service, not just a pose tree. Revision 2 specifies both: one
   `Pose` per node for construction, and a shared `FrameGraph`/`FrameView` that
   preserves `transform(P, from_frame, to_frame)`, aliases and virtual frames.

It also adds the **pyg4ometry bridge** as the recommended Geant4 backend, which
makes the "circles, not boxes" case and future solids cheap.

**Revision 4 (2026-11-06)** changes the delivery order only: specs + CMS source
come first, the runtime model second; `VolumeSink` moves to the first exporter
(Phase 5); CLI/YAML are dropped and the event layer is optional. The same
revision also corrects the terminology: **the XML `<Wire>` is the cell entry;
there is no separate wire object**. The delivery detail is in
[`.agents/plan.md`](../../.agents/plan.md) Rev 4.

---

## 0. TL;DR

The missing boundary is still the same: **a declarative detector description
separate from the CMS XML**. The description models three things explicitly:

> **topology** (which node contains which), **solid** (what volume it is,
> including a cell), and **pose** (where it sits).

The CMS XML becomes one *source* that produces this description; pyg4ometry
becomes one *backend* that consumes it. Neither leaks into the core.

The runtime pieces:

- `Node` tree: `Detector → Station → SuperLayer → Layer → Cell`; any node may
  own a solid, or be a pure grouping frame.
- `Shape`: `Box`, `Tube` (and an extension hook); dimensions in the node's
  local axes; `aabb()` derived for placement/overlap.
- `CellGrid`: pitch, count, **stagger**, first id; generates `Cell` nodes.
- `Pose`: one per node, `p_parent = R·p_child + t`; `world_pose` composed
  top-down once.
- `FrameGraph`: shared named-frame graph (`Cell → Layer → SL2 → Station →
  CMS`), with scoped aliases and virtual frames; `obj.transformer` returns a
  `FrameView` so the existing API keeps working.
- **Backend seam, no pyg4ometry yet:** exporters consume a `VolumeSink` and
  already-folded placements; `mpldts/export/pyg4ometry.py` can be added later
  as an optional extra (`mplDTs[g4]`) without touching the core or the specs.
- **Physical volumes are explicit:** station, cells, honeycomb and yoke are
  solids; super layers and layers are grouping frames. There is no separate
  wire volume because there is no separate wire object.
- **Event objects are a separate layer:** segments (already implemented),
  muon tracks and jets/cones are annotations on a frame, not detector solids.
  They reuse the frame graph and are developed after the geometry core.

A prototype already demonstrates the model: box cells and tube cells in one
detector, stagger, frame-graph round-trips, JSON round-trip and exporter pose
folding, all at machine precision.

---

## 1. What the current code does

### 1.1 Object model

```
DTFrame (id, parent, number, bounds, local_center, global_center, direction)
 ├── Station      (wheel, sector, number)       -> CMS chamber
 │    └── SuperLayer (rawId, parent)            -> CMS super layer
 │         └── Layer (rawId, parent)            -> CMS layer
 │              └── DriftCell (number, parent)  -> CMS "wire" entry == cell centre
 └── Segment / AMDTSegment
```

`bounded` by `DTGEOMETRY`, a 20.8 MB XML singleton parsed at import
(`_geometry.py:196`). There is no writer and no shape abstraction; the XML
`<Wire>` is already the cell entry.

### 1.2 The terminology in the XML

For each `<Layer>`, the XML contains a `<Wires>` element with:

```xml
<Wires width="4.19999981" thickness="1.29999995" length="234.800003" first="1" last="49"/>
<Wire wireNumber="1" LocalPosition="(-102.4, 0, 13.7)" GlobalPosition="(...)"/>
```

- `Wires.width/thickness/length` are the **cell box** dimensions (pitch,
  drift gap, cell length).
- Each `<Wire>` is a **cell entry**: its id and its local/global position.
- The `wireNumber` is the cell id used by the current `DriftCell`.

So the current `DriftCell(number)` is the cell, and the XML element name
`Wire` is only historical. There is no second object to model.

### 1.3 Construction path and CMS coupling

| Class | Line | Reads from `DTGEOMETRY` |
|---|---|---|
| `Station.__init__` | `station.py:50-54` | rawId, LocalPosition, GlobalPosition, NormalVector, Bounds |
| `Station._build_station` | `station.py:191` | iterates `SuperLayer` children |
| `SuperLayer.__init__` | `super_layer.py:35-38` | number, positions, bounds |
| `SuperLayer._build_super_layer` | `super_layer.py:90` | iterates `Layer` children |
| `Layer.__init__` | `layer.py:35-40` | number, positions, bounds, cell-id range |
| `Layer._build_layer` | `layer.py:99-112` | cell size + every `<Wire>` entry |
| `DriftCell.__init__` | `drift_cell.py:54-56` | cell size + positions (again) |

CMS rules in the core: wheel/sector/station ranges (`station.py:147-176`),
face orientation (`station.py:110-123`), sector-φ and MB4 (13/14)
(`station.py:249-271`), SL13 frame (`station.py:273-286`), and the SL2 90°
special case (`super_layer.py:99-103`).

---

## 2. Findings that drive the design

### 2.1 Correctness

**(a) SL2 transform chain is wrong by `√2·|SL_local_x|`.** Measured 2.475 cm
(W−2/S1/MB2), 0.424 cm (W0/S5/MB3), 0.707 cm (W−2/S2/MB1). `Layer` subtracts a
station-frame translation from an SL-frame one (`layer.py:137-143`), and
`DriftCell` inherits the error (`drift_cell.py:87-93`). The stored XML
`global_center` is right; the composed transform is not. The new pose-per-node
model removes the possibility of mixing frames.

**(b) Cache mutates shared geometry.** `StationsCache.get(..., dt_info=...)`
returns the same `Station` and writes onto shared `DriftCell`s
(`station.py:386-387`, `:288-325`). Event A's values leak into event B.
Geometry must be immutable; per-event data belongs in an overlay.

**(c) Attribute-order-dependent parsing.** `_geometry.py:122` and `:126` use
`element.attrib.values()` positionally; `layer.py:101` does the same for `<Wire>` entries.
Reordering legal XML changes `bounds` or `WiresSize`. Use explicit keys.

**(d) `bounds` assumes a box.** `DTFrame.width/height/length` and
`local_cords_at_min` assume rectangular extents, and the G4 generator reorders
them (`generate_geometry_data.py:68`). A `Tube` cell cannot be represented
correctly: its dimensions are `(radius, length)`, its AABB is derived. The new
model separates `shape.dimensions` from `shape.aabb()`.

**(e) Version/frame-name divergence.** Installed 2.2.0-beta names the SL frame
`"SuperLayer"`; the checked-out branch names it `"SL{n}"`
(`super_layer.py:115`). The generator asks for `"SuperLayer"`
(`generate_geometry_data.py:131`), so installing the branch breaks every SL2
station. No test covers this. `pyproject` says 2.1.0, `__version__` says
2.2.0-beta.

### 2.2 Performance

Measured on 2026-11-06. The checkout (`enhancement-cacheObjects`) already
indexes the XML at parse time; the installed 2.2.0-beta does not. State which
package a number comes from.

| measurement | checkout | installed 2.2.0-beta |
|---|---|---|
| geometry import + XML parse/index | ~3.4 s | not measured |
| `Station(-2,1,2)` | 1.00 s | 1.25 s |
| `Station(2,14,4)` | 0.71 s | 2.26 s |
| `Station(0,1,1)` | 0.87 s | 1.66 s |
| all 250 (extrapolated) | ~3–4 min | ~7–10 min |

The generator still builds each station 2–3×. Per-cell `TransformManager`
construction and the XPath scans are the remaining cost. The old profile
numbers (3.75 s `ElementTree.find`, 2.64 s `get_transformation`) came from the
pre-index code and are not reproducible on the branch; they are retired. One
pose per node + a shared frame graph + vectorized grids should reach
**< 20 ms/station**.

### 2.3 Conceptual

- The XML `<Wire>` is already the cell; no separate wire object is needed.
- `Shape` does not exist; `bounds` is a tuple with implicit box semantics.
- The per-object `TransformManager` copies sub-chains (`layer.py:116-143`,
  `drift_cell.py:63-93`), so names are duplicated and stale copies do not see
  parent changes. A shared graph fixes both ambiguity and cost.
- The exporter knows CMS internals (`SL2` rotation, MB4, honeycomb gap), which
  is a symptom of missing `shape`/`pose` concepts.

---

## 3. Concepts and terminology (the part revision 1 got wrong)

| Concept | Meaning | Current code | New model |
|---|---|---|---|
| **Detector / assembly** | root that holds stations in a world frame | none (CMS global hard-coded) | `DetectorSpec` / `FrameGraph` root |
| **Station / chamber** | one DT chamber | `Station` | `Station` node + optional solid |
| **Super layer** | stack of layers, one cell orientation | `SuperLayer` | `SuperLayer` node |
| **Layer** | one plane of cells | `Layer` | `Layer` node |
| **Cell** | gas/drift volume and its centre; XML `<Wire>` is a cell | `DriftCell` | `Cell` node with `Shape` |
| **Cell grid** | repetition of cells (pitch, count, stagger, ids) | loop over XML `<Wire>` entries | `CellGrid` |
| **Shape / solid** | box, tube, trapezoid, ... | implicit box via `bounds` | `Shape` (`Box`, `Tube`, ...) |
| **Honeycomb** | passive aluminium box between super layers | generator-only | `StationSpec.attachments` (`SolidSpec`) |
| **Yoke** | iron structure with station-shaped holes | generator-only | `DetectorSpec.structures` (`StructureSpec`) |
| **Pose** | rigid transform child → parent | mixed `local_center` + `TransformManager` | `Pose` per node |
| **Frame graph** | named-frame point transformations | per-object `TransformManager` copies | shared `FrameGraph` + `FrameView` |
| **Material** | gas, air, aluminium, tungsten | only in the G4 generator | `material` on nodes |

```
DetectorSpec (world)
├── structures: StructureSpec  [yoke, CSG payload]     physical
└── StationSpec                [solid: Box air]        physical
    ├── attachments: SolidSpec [honeycomb box]         physical
    └── SuperLayerSpec         [solid: None]           grouping
        └── LayerSpec          [solid: None]           grouping
            └── CellGrid → CellSpec [solid: Box|Tube]  physical

Event layer (separate): Segment / Track / Jet  (frame + attributes)
```

Nodes with `solid=None` are pure grouping frames: they matter for
transformations and plotting, but produce no Geant4 volume. That is exactly
what CMS SL/layer nodes are today, and it keeps the G4 hierarchy shallow.

---

## 4. Target model

### 4.1 Topology: nodes with optional solids

```python
@dataclass
class Node:
    name: str
    kind: str                  # detector | station | superlayer | layer | cell
    pose: Pose                 # parent-relative
    shape: Shape | None        # None = grouping frame
    material: str | None
    parent: Node | None
    frame_id: str              # unique path, e.g. "/CMS/W-2/S1/MB2/SL2/L1/C7"
    children: list["Node"]
```

Runtime subclasses add accessors (`station.super_layer(2)`,
`layer.cell(7)`), but the builder is generic. A node with no shape contributes
its pose to its children and nothing else.

Why optional solids matter:

- CMS: station air box → cells directly; SL/layer are grouping.
- A test-beam telescope: layer envelopes may be physical gas boxes, or not.
- A tube-cell chamber: cells are cylinders placed directly in the station air.
- The exporter decides which levels become volumes; the physics decides which
  levels need material.

### 4.2 Shapes

```python
class Shape:
    def aabb(self) -> tuple[float, float, float]: ...   # full extents
    def volume(self) -> float: ...
    def symmetry_axis(self) -> str | None: ...          # backend-neutral hook

@dataclass(frozen=True)
class Box(Shape):
    dx: float; dy: float; dz: float

@dataclass(frozen=True)
class Tube(Shape):
    radius: float
    length: float
    axis: str = "y"            # cell length axis
    inner_radius: float = 0.0  # >0 for a shell
```

`Box(dx,dy,dz)` is the CMS cell `Box(4.2, 234.8, 1.3)`: x = pitch, y = cell
length, z = drift gap. `Tube(radius=2.2, length=234.8, axis="y")` is the
cylindrical cell from the user's example.

`aabb()` is used for placement, overlap checks and the legacy `bounds`
property; `dimensions` (the shape fields) is what an exporter or a designer
uses. Never derive a tube from a box tuple again.

Extension hook: a `Shape` only needs `aabb`, `volume` and `symmetry_axis`.
The backend maps the latter to its own native frame (Geant4 `Tubs` is along
+z, hence a z→y rotation for a y-axis tube). `Trapezoid`, `Trd`, `Polycone`,
`Extruded` can be added one at a time. **Do not implement CSG** (`Union`,
`Subtraction`, `Intersection`) in mplDTs; pyg4ometry already has them, and a
future backend can accept a pre-built pyg4ometry solid. That is the boundary.

### 4.3 Cells and cell grids

```python
@dataclass
class CellGrid:
    pitch: float
    count: int
    shape: Shape                 # template, e.g. Box(...) or Tube(...)
    first_id: int = 1
    offset: float = 0.0          # extra shift along x, cm

    def x_positions(self) -> np.ndarray:
        i = np.arange(self.count)
        return self.offset + (i - (self.count - 1) / 2) * self.pitch
```

The CMS pattern is captured without special cases:

| layer | count | first id | offset |
|---|---|---|---|
| 1 | 49 | 1 | 0 |
| 2 | 50 | 1 | 0 |
| 3 | 49 | 1 | 0 |
| 4 | 48 | 2 | 0 |

All four grids are centred on the layer frame (`offset = 0`); the
half-cell stagger falls out of the cell-count parity (49/50/49/48), not from
an explicit offset. Measured from `DTGeometry_v3.xml`, pitch 4.2, every grid
centred at x = −1.6 in the super-layer frame: L1 −102.4…99.2, L2 −104.5…101.3,
L3 −102.4…99.2, L4 (48 cells, first id 2) −100.3…97.1.

The XML `<Wire>` element is the **cell entry** (number + position), mapped
once by the CMS source. A cell is the gas/drift volume; its centre is that
position. There is no separate wire object, and no exporter emits one.

### 4.4 Materials

Add `material: str | None` to nodes. The core only carries the name; the
backend resolves it (`G4_AIR`, `GAS_MIXTURE`, `G4_Al`, `G4_W`, ...). This keeps
mplDTs independent of Geant4 material construction and lets pyg4ometry or the
simulator own the material map.

### 4.5 Pose convention (unchanged, now applied to all nodes)

> **Every node stores one pose relative to its parent:
> `p_parent = R · p_child + t`. Sizes are full extents in the node's own local
> frame. Global poses are derived top-down and cached.**

For a cell:

```
world_C = T_world_det · T_det_station · T_station_sl · T_sl_layer · T_layer_cell
```

The SL2 "rotation" is simply `T_station_sl = Rz(90°)`; no `if number == 2`.
The CMS XML's mixed local/global positions are converted by the source into
parent-relative poses (see §5).

---

## 5. Transformations: how `transformer` works in the new model

This is the part that was unclear in revision 1. There are **two services**,
and they must not be confused.

### 5.1 Construction: the pose tree

The builder composes `world_pose` once, top-down:

```python
def build_node(spec, parent_pose, parent_frame, graph):
    world = parent_pose.compose(spec.pose)
    node.world_pose = world
    graph.add_edge(node.frame_id, parent_frame, spec.pose)
    for child in spec.children:
        build_node(child, world, node.frame_id, graph)
```

- `pose` is the single source of truth; `world_pose` is derived and cached.
- Cost is O(nodes), not O(cells × path length); 60k cells is fine.
- Moving a node is `node.set_pose(new_pose)`, which updates its edge, recomputes
  the subtree and invalidates the graph cache. Until then, geometry is
  immutable and safe to share.

### 5.2 Queries: the shared `FrameGraph`

The current API allows arbitrary named-frame conversions:

```python
station.transformer.get_transformation("Station", "CMS")
cell.transformer.transform(point, "Cell", "Layer")
station.transformer.transform(p, "StationNvPhi", "Station", type="vector")
```

The replacement is a graph with one edge per parent/child pose:

```python
class FrameGraph:
    def add_edge(self, child, parent, pose): ...
    def add_virtual(self, name, relative_to, pose): ...   # SL13Center, StationNvPhi
    def matrix(self, from_frame, to_frame) -> Pose: ...    # BFS + cache
    def transform(self, P, from_frame, to_frame, kind="point"): ...
```

- Edges store `pose_child_in_parent`; the reverse edge stores its inverse.
- `matrix` is a BFS that composes poses, cached by `(from, to)`; invalidated
  when an edge changes.
- Points get translation; vectors (`type="vector"`) get rotation only. This is
  the same distinction the current code makes.
- Virtual frames are edges that do not correspond to a geometry node. The CMS
  preset registers `StationNvPhi`, `StationNvEta`, `SectorRef` and
  `SL13Center`; the core does not know them.

### 5.3 Per-object view and aliases

`obj.transformer` returns a `FrameView` bound to that object:

```python
class FrameView:
    def _resolve(self, name): ...            # scoped alias -> full frame id
    def get_transformation(self, a, b): ...  # 4x4 ndarray
    def transform(self, P, a, b, type="point"): ...
    @property
    def available_frames(self): ...
```

Aliases are resolved **in the object's scope**, so `"Layer"` means *this*
cell's layer, `"SL2"` means *this* station's SL2, and `"CMS"`/`"World"` means
the root. Full frame ids are unique paths, so the graph is unambiguous:

```
World/CMS/W-2/S1/MB2/SL2/L1/C7
```

Backward-compatible aliases: `Station`, `SuperLayer`, `SL{n}`, `Layer`, `Cell`,
`CMS`, `World`. `"SuperLayer"` and `"SL{n}"` both resolve, which closes the
current version break. If a name is ambiguous in a scope (e.g. `"Layer"` from a
station view), raise a clear `KeyError` listing the available aliases.

### 5.4 Mapping the current code

| Current | New |
|---|---|
| `station.transformer` | `FrameView(graph, station)` |
| `get_transformation("Station","CMS")` | graph path `station.frame_id → root` |
| `cell.transformer.transform(p,"Cell","CMS")` | alias `Cell` → cell id, `CMS` → root |
| `sl.transformer.get_transformation("SuperLayer","Station")` | alias `SuperLayer`/`SL{n}` → sl id |
| `station.transformer.add(...)` for virtual frames | `graph.add_virtual(...)` by the CMS preset |
| `station.transformer.add/remove(...)` by users | delegate to `graph.add_edge` / `remove_edge` under a scoped name |
| `__str__` | list the frames in scope |
| per-object `TransformManager` copies | one shared graph; no copies |
| `available_frames` | aliases in scope + full paths |

The old `TransformManager` can be kept as a deprecation shim implemented on top
of `FrameGraph`, or removed in 3.0. The public signature stays. `FrameView`
implements `add`, `remove`, `get_transformation`, `transform`, `available_frames`
and `__str__` so existing call sites keep working; `add`/`remove` are thin
wrappers over graph edges with scoped names.

Two compatibility details worth fixing explicitly:
`get_transformation` keeps the current contract (warn and return `None` when no
path exists), while `transform` raises a `ValueError`; and `transform` accepts
`type="point"` (default) or `type="vector"`, with the same meaning as today.

### 5.5 What this fixes

- **SL2 frame mixing**: no subtraction of coordinates from different frames;
  each node has one pose.
- **Ambiguous names**: aliases are scoped; full ids are paths.
- **Stale copies**: one graph, one source of truth.
- **Per-cell cost**: no `TransformManager` per cell; only two edges per cell in
  the graph, and `world_pose` is computed during the build.

---

## 6. The CMS XML becomes a source

`mpldts/geometry/sources/cms_xml.py` implements `GeometrySource` and emits
`StationSpec`:

1. Index chambers by `(wh, sec, st)`, SL/layers by `rawId`, and **cell centres
   per layer** at parse time (no `.//Wires` inside loops).
2. For each layer, read `WiresSize` by name:
   `Box(width, length, thickness)` (x, y, z) and `WiresRange` (first, last).
3. Compute `CellGrid`:
   - `pitch = width` (4.2 cm),
   - `count = last − first + 1`,
   - `first_id = first`,
   - `offset` from the first cell's local x relative to the layer centre.
4. Compute parent-relative poses from the XML local/global data and the known
   orientation; **do not trust** the mixed station/SL frames. The XML
   `GlobalPosition` of every cell is retained as `metadata["reference"]`.
5. Emit `StationSpec` with `shape=Box(station bounds)` and
   `material="G4_AIR"`; SL/layer shapes stay `None` (grouping) unless a
   physical envelope is requested.

**The oracle:** rebuild all 250 chambers from specs and compare each computed
cell centre with the XML `GlobalPosition`. Require max error < `1e-3` cm. This
catches the SL2 bug and any future pose regression. It is also the safest way
to migrate the plotting library: if the computed globals match the XML, the
rewrite is behaviour-preserving.

The `<Wire>` naming is handled once, here: XML `<Wire>` → cell entry (id +
position). No other layer of the code sees the historical name.

---

## 7. Assemblies and serialization

```python
@dataclass
class DetectorSpec:
    name: str
    pose: Pose
    stations: list[StationSpec]
    shape: Shape | None        # optional world envelope
    material: str = "G4_Galactic"
```

- `DetectorSpec` is the root; `"CMS"` is just the default name of the world
  frame for CMS geometries, preserving `to_frame="CMS"`.
- `build_detector(spec)` creates one `FrameGraph` and one `Station` per entry.
- JSON schema version `mpldts.detector/2`; the shape is explicit; derived
  fields (centres, world poses) are never stored.

```json
{
  "schema": "mpldts.detector/2",
  "name": "TB-2026",
  "pose": {"rotation": [...], "translation": [0,0,0]},
  "stations": [{
    "name": "TB-1",
    "pose": {"rotation": [...], "translation": [50,0,0]},
    "shape": {"kind": "box", "dx": 108.8, "dy": 110.0, "dz": 40.0},
    "material": "G4_AIR",
    "super_layers": [{
      "number": 1,
      "pose": {"rotation": [...], "translation": [0,0,8]},
      "layers": [{
        "number": 1,
        "pose": {"rotation": [...], "translation": [0,0,-1.95]},
        "grid": {
          "pitch": 4.2, "count": 24, "first_id": 1, "offset": 0.0,
          "shape": {"kind": "box", "dx": 4.2, "dy": 100.0, "dz": 1.3}
        }
      }]
    }]
  }]
}
```

For a tube cell, replace the shape with
`{"kind": "tube", "radius": 2.2, "length": 100.0, "axis": "y"}`.

---

## 8. pyg4ometry readiness (deferred)

The bridge is **not part of the current delivery**. The goal now is to leave
the seams so that adding it later is a new module, not a refactor.

### 8.0 What the prototype proves (no dependency)

1. **`VolumeSink` protocol.** The prototype defines the contract; the library
   implements it with the first exporter (`TgSink`, Phase 5), not before — a
   protocol with no implementation is speculative. The core produces
   `VolumePlacement`s (`node`, `mother`, folded `pose_in_mother`). Any
   backend — pyg4ometry, a `.tg` writer, GDML, a test double — implements
   three methods:

   ```python
   class VolumeSink(Protocol):
       def begin(self, root: Node) -> None: ...
       def place(self, node: Node, mother: Node | None,
                 pose_in_mother: Pose) -> None: ...
       def end(self) -> None: ...

   def export_volumes(root: Node, sink: VolumeSink) -> None:
       sink.begin(root)
       for p in iter_volume_placements(root):
           sink.place(p.node, p.mother, p.pose_in_mother)
       sink.end()
   ```

   The prototype ships a `RecordingSink` and asserts that it receives exactly
   the same 193 placements as the planner. Phase 5 adds
   `mpldts/export/base.py` + `RecordingSink` + `TgSink`; a future
   `PyG4ometrySink(VolumeSink)` lives in `mpldts/export/pyg4ometry.py`.

2. **Backend-neutral shapes.** `Shape` exposes `aabb()`, `volume()` and
   `symmetry_axis()`; it never imports Geant4 or pyg4ometry. The z→y mapping
   for `Tubs` is a backend adapter (`g4_alignment(shape)` in the prototype),
   not a method on the shape.

3. **`Pose.matrix` is a 4×4 homogeneous transform.** Any backend can use it
   directly, or convert it with its own Euler-angle routine. pyg4ometry's
   `transformation.matrix2tbxyz` is the converter to use later; the exporter
   test will assert `tbxyz2matrix(matrix2tbxyz(R)) == R`.

4. **Specs are the only input.** The JSON schema (`mpldts.station/2`,
   `mpldts.detector/2`) and `iter_volume_placements` do not depend on the
   backend. The `.tg` exporter can be migrated to the same sink before
   pyg4ometry exists.

5. **Optional namespace reserved.** `mpldts/export/` is not imported by the
   core; `pyg4ometry` will be an optional extra (`mplDTs[g4]`), never a core
   dependency.

6. **No backend names in the model.** `Station`, `Layer`, `Cell`, `Shape`,
   `Pose` and `FrameGraph` are physics/geometry concepts only.

**Compatibility contract:** a future bridge must be implementable by adding
`mpldts/export/pyg4ometry.py` (plus an optional dependency and tests) without
changing `specs.py`, `model.py`, `builder.py` or the public constructors.

### 8.1 Why pyg4ometry is the right backend (when we do it)

pyg4ometry already provides exactly what a generalized mplDTs should not
reimplement:

- all Geant4 solids (`Box`, `Tubs`, `Trap`, `Trd`, `Polycone`, `Extruded`,
  booleans, ...), with full-length constructors ([`Box`](https://github.com/g4edge/pyg4ometry/blob/main/src/pyg4ometry/geant4/solid/Box.py), [`Tubs`](https://pyg4ometry.readthedocs.io/en/v1.2.0/autoapi/pyg4ometry/geant4/solid/Tubs/));
- `LogicalVolume` / `PhysicalVolume` placements with rotations and units
  ([`PhysicalVolume`](https://pyg4ometry.readthedocs.io/en/v1.2.0/autoapi/pyg4ometry/geant4/PhysicalVolume/));
- materials, GDML writing, VTK visualisation, overlap checking;
- a clean route from Python to GDML, which Geant4 loads with `G4GDMLParser`.

The bridge is therefore a *tree walk plus a mapping table*, not a new geometry
engine.

### 8.2 Mapping

| mplDTs | pyg4ometry |
|---|---|
| `Box(dx,dy,dz)` | `g4.solid.Box(name, dx, dy, dz, reg, lunit="cm")` (full lengths) |
| `Tube(radius, length, axis="y")` | `g4.solid.Tubs(name, 0, radius, length, 0, 2π, reg, lunit="cm")` + z→y adapter (`symmetry_axis`) |
| `Node.shape` | solid + `g4.LogicalVolume(solid, material, name, reg)` |
| `Node.pose` | `g4.PhysicalVolume([rx,ry,rz], [x,y,z,"cm"], lv, name, mother, reg)` |
| grouping node (`shape=None`) | no volume; fold its pose into children, or use `AssemblyVolume` |
| `material="G4_AIR"` | `LogicalVolume(..., "G4_AIR", ...)` (string is resolved as a predefined material) |
| `Detector` | world `LogicalVolume` + `reg.setWorld(...)` |
| honeycomb / yoke | passive solids / structures (see §14) |

### 8.3 Rotation conversion (the only subtle part)

pyg4ometry's `PhysicalVolume` takes Tait-Bryan angles `[rx, ry, rz]`, not a 3×3
matrix. It ships the exact converter:

```python
from pyg4ometry import transformation as tr

R = pose_in_mother.rotation_matrix          # 3x3, child -> mother
angles = tr.matrix2tbxyz(R)                 # [rx, ry, rz]
assert np.allclose(tr.tbxyz2matrix(angles), R)
```

This round-trip must be an assertion in the exporter tests. It is the single
place where a convention (active vs passive) can silently mirror the geometry.

### 8.4 Exporter sketch (future)

The sketch below is the target shape of the future module; it is not
implemented in the current delivery.

```python
def to_pyg4ometry(detector: DetectorSpec, materials, lunit="cm"):
    import pyg4ometry
    from pyg4ometry import geant4 as g4
    from pyg4ometry import transformation as tr

    reg = g4.Registry()
    world = make_world(g4, reg, detector)
    volumes = {}

    for pl in iter_volume_placements(detector):   # pre-order, grouping folded
        node = pl.node
        if node.shape is None:
            continue
        solid = make_solid(node.shape, node.name + "_solid", reg, lunit)  # backend adapter
        lv = g4.LogicalVolume(solid, node.material or "G4_AIR", node.name + "_lv", reg)
        volumes[node.frame_id] = lv

        mother = volumes[pl.mother.frame_id] if pl.mother else world
        rot = tr.matrix2tbxyz(pl.pose_in_mother.rotation_matrix)
        pos = list(pl.pose_in_mother.translation) + ["cm"]
        g4.PhysicalVolume(list(rot) + ["rad"], pos, lv,
                          node.name + "_pv", mother, reg)

    return reg
```

`iter_volume_placements` folds poses through grouping nodes, so a cell's
placement is relative to the nearest ancestor that has a volume (the station in
the CMS case). This is the same walk the `.tg` exporter needs; only the backend
differs.

### 8.5 Output and Geant4 integration

```python
reg = to_pyg4ometry(detector, materials)
writer = pyg4ometry.gdml.Writer()
writer.addDetector(reg)
writer.write("geometry/detector.gdml")
```

Then in `DetectorConstruction`:

```cpp
G4GDMLParser parser;
parser.Read("geometry/detector.gdml");
G4VPhysicalVolume* world = parser.GetWorldVolume();
```

This can replace `G4tgbVolumeMgr` for the DT part, or coexist while the `.tg`
path is still needed for the yoke. GDML is hierarchical, handles rotations and
units natively, and is easier to generate than hand-written `.tg`.

### 8.6 Validation and limitations

- **Round-trip**: `tbxyz2matrix(matrix2tbxyz(R)) == R`; compare solid AABBs
  with `shape.aabb()`; compare built cell centres with the spec.
- **Overlaps**: `logical_volume.checkOverlaps(recursive=True)` (pyg4ometry
  provides it).
- **Visual**: `pyg4ometry.visualisation.VtkViewer` for a quick look.
- **Dependency weight**: pyg4ometry pulls VTK/CGAL; make it an optional extra
  (`pip install mplDTs[g4]`) and keep the core numpy-only. The bridge module
  must import lazily and fail with a clear message.
- **Placement**: prefer `mpldts/export/pyg4ometry.py` (optional) or
  `DTG4Simulator/geometry/exporters/`. Do not put pyg4ometry in the core.
- **Not a replacement for physics**: materials, sensitive volumes, fields and
  digitization stay in the simulator.

### 8.7 Why this also answers the "tube cell" case

`Tube(radius, length, axis="y")` → `g4.solid.Tubs` with a z→y alignment
rotation. Nothing in the core assumes a box; only the shape adapter knows that
`Tubs` is built along z.

---

## 9. API sketches

### 9.1 A custom box station

```python
spec = StationSpec(
    name="TB-1",
    pose=Pose.rotated_z(15, (50, 0, 0)),
    shape=Box(108.8, 110.0, 40.0),
    material="G4_AIR",
    super_layers=[
        SuperLayerSpec(1, Pose.translated(0, 0, +8), layers=[
            LayerSpec(i + 1, Pose.translated(0, 0, -1.95 + 1.3 * i), shape=None,
                      cells=CellGrid(pitch=4.2, count=24,
                                     shape=Box(4.2, 100.0, 1.3)))
            for i in range(4)
        ]),
        SuperLayerSpec(2, Pose.rotated_z(90, (0, 0, -8)), layers=...),
    ],
)
station = build_station(spec, graph)
```

### 9.2 A tube-cell station

```python
cells = CellGrid(
    pitch=5.0, count=16,
    shape=Tube(radius=2.2, length=100.0, axis="y"),
)
```

### 9.3 Transform queries (the old API, preserved)

```python
station.transformer.transform([0, 0, 0], "Station", "CMS")
cell.transformer.transform(point, "Cell", "Station")
cell.transformer.transform(direction, "Cell", "CMS", type="vector")
station.transformer.get_transformation("StationNvPhi", "Station")
```

### 9.4 Export

```python
from mpldts.export.pyg4ometry import to_pyg4ometry
reg = to_pyg4ometry(detector_spec, materials={"G4_AIR": ..., "GAS": ...})
```

---

## 10. Delivery order and tickets (revision 4)

**Plan Rev 4 and the tickets were approved on 2026-11-06; Phase 0 is in
progress.** The canonical backlog is [`.agents/TICKETS.md`](../../.agents/TICKETS.md);
checkpoints are tracked in [`.agents/PROGRESS.md`](../../.agents/PROGRESS.md).

| Phase | Goal | Exit criterion | Tickets |
|---|---|---|---|
| 0 | Safety net | invariant + node snapshot + `.tg` smoke + CI | T-001, T-003, T-005, T-006, T-007 |
| 1 | Specs + CMS source | spec oracle green for all 250 chambers | T-010, T-011, T-012 |
| 2 | Runtime model + compatibility | public-API oracle green; `< 20 ms`; no XML in model | T-020…T-024 |
| 3 | Assemblies + custom stations + extras | custom 1-SL/5-SL; honeycomb; yoke data hook | T-030…T-033 |
| 4 | Event annotations (optional) | legacy `Segment` API + tracks/jets | T-040…T-042 |
| 5 | Authoring + JSON + `.tg` | JSON → build → plot → `.tg`; parity | T-050, T-051, T-052, T-054 |
| 6 | Future: pyg4ometry + GDML | deferred; additive via `VolumeSink` | T-060 |

**Phase 0 — safety net (1–2 days).** pytest, the transform invariant/oracle
harness with a node snapshot over representative chambers (SL2 `xfail`),
downstream pin + `.tg` smoke, benchmark, branch/CI baseline. Nothing else starts until this is green.

**Phase 1 — specs + CMS source (4–6 days).** `Pose`, `Shape`/`Box`/`Tube`,
`CellGrid`, the `*Spec` dataclasses; `CMSXMLSource` with parse-time indexes,
explicit attributes and parent-relative poses; the spec oracle over all 250
chambers. The runtime classes are untouched.

**Phase 2 — runtime model (7–10 days).** Topology with optional solids,
`build_station` (detector assembly is Phase 3), `FrameGraph`/`FrameView`, legacy
constructors delegating, SL2 fixed, immutable cache/overlay, performance pass,
`DTGEOMETRY` shim. This is the critical path.

**Phase 3 — assemblies and extras (4–6 days).** Runtime `DetectorSpec` and
assemblies, custom 1-SL/5-SL stations, CMS preset remainder (virtual frames,
MB4 13/14), plotting by orientation, honeycomb attachment. The yoke gets a
data hook only; it remains in `DTG4Simulator` until a CSG backend exists.

**Phase 4 — event annotations (3–5 days, optional).** Refactor
`Segment`/`Segments` onto a generic annotation layer; add `Track` and
`Jet`/`Cone`; collections and plotting adapters. It depends on Phase 2
(frames), not on Phases 3/5. It can be deferred without affecting the geometry
delivery.

**Phase 5 — authoring and `.tg` (4–6 days).** Convenience builders, JSON schema
`mpldts.detector/2`, validation, and `VolumeSink` + `RecordingSink` +
`TgSink` that proves the exporter seam without pyg4ometry. `DTG4Simulator`
switches to the spec path when the output matches. No CLI in this revision.

**Phase 6 — future (deferred, 5–8 days).** `mpldts/export/pyg4ometry.py`, GDML,
`G4GDMLParser`. Entry criteria: Phases 0–5 merged and an explicit ADR update.

**Dependencies.** 0 → 1 → 2 → {3, 4, 5}. Phase 4 can start after 2 and run in
parallel with 3/5. Phase 3's yoke CSG waits for a backend; the honeycomb is
independent. Phase 6 waits for everything.

**Estimate.** Phases 0–2 (critical path): ~2–3 weeks part-time. Phases 0–5:
~4–6 weeks part-time. Phase 6 is excluded.

**GitHub workflow.** One ticket → one branch → small commits → PR → review →
merge. Branch names `feature/T-0xx-<slug>`, commits `T-0xx: <imperative>`, PRs
use the repository template and link the ticket. Details in
[`.agents/workflow.md`](../../.agents/workflow.md). Do not commit directly to
`main`.

## 11. Tests and invariants

**Unit**
- `Pose` composition/inverse/point-vs-vector.
- `Box`/`Tube` AABB and volume; `Tube` symmetry-axis adapter.
- `CellGrid` positions, stagger, first id; 49/50 pattern.
- The XML `<Wire>` maps to a `Cell`; no separate wire object exists.
- JSON round-trip for box and tube stations; attachments round-trip.

**Graph**
- Full path vs alias; inverse round-trip; vector vs rotation column.
- `"SuperLayer"` and `"SL2"` both resolve.
- Virtual frame (`StationNvPhi`, `SL13Center`).
- Ambiguous alias raises a clear error.

**CMS oracle**
- All 250 chambers, cell centres vs XML `GlobalPosition`, `1e-3` cm.
- SL2 specifically.

**Export**
- Folded placement of every cell equals its `world_pose`.
- Backend seam: `RecordingSink` receives exactly the planned placements.
- `g4_alignment`: box→identity, tube axis y→`R_x(-90)`, tube axis x→`R_y(90)`.
- No separate wire object exists; honeycomb is emitted; a yoke structure is
  either exported by a CSG-capable backend or rejected explicitly.
- `.tg` sink parity with the current generator (Phase 5).
- Future (Phase 6): pyg4ometry rotation round-trip, solid AABB vs
  `shape.aabb()`, GDML load, overlap check.

**Event objects**
- `Segment` legacy fields and transforms; `AMDTSegment` unchanged.
- `Track` polyline, `Jet` cone, collection filter/groupby, JSON round-trip.
- Annotations never enter the detector spec or the geometry exporter.

**Performance**
- One station < 50 ms after Phase 1, < 20 ms after Phase 2; full CMS < 10 s;
  no per-cell `TransformManager`.

---

## 12. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Pose convention changes late | high | freeze `Pose` + axis rule in phase 2; oracle tests |
| SL2/mixed frames reveal more issues | medium | XML globals as ground truth; fix the source |
| Shape API over-fitted to boxes | medium | `Box` + `Tube` first; extension hook; pyg4ometry for exotic solids |
| pyg4ometry dependency/platform (future) | medium | deferred; seam tested with `RecordingSink`; optional extra, lazy import |
| Rotation active/passive mismatch | high (mirrored geometry) | `matrix2tbxyz` round-trip + AABB tests |
| Grouping vs physical volumes | medium | explicit `shape=None`; exporter folds; overlap checks |
| Backward-compat aliases | medium | scoped `FrameView`, deprecation warnings |
| Cache mutation | medium | immutable specs; per-event overlay |
| Scope creep into CSG | high | boundary: primitives only; CSG via pyg4ometry |
| Yoke CSG blocks the geometry pipeline | medium | keep yoke in the simulator until a CSG backend; `StructureSpec` hook only |
| Event layer becomes a full event model | medium | annotation bag + three types only; separate schema; Phase 4 |
| `.tg` parity regression | high | golden station output; switch the generator only after parity |
| Two sources of truth | high | spec is the only input; retire the old generator path |

---

## 13. Maintainer decisions (2026-11-05)

The questions from revision 2 are now answered. The corresponding ADRs are in
[`.agents/decisions.md`](../../.agents/decisions.md).

1. **Physical volumes:** station, cells, honeycomb and yoke are physical.
   Super layers and layers are grouping frames. There is no separate wire
   object (ADR-011, ADR-019).
2. **Shapes:** only `Box` is required now. Leave the `Shape` protocol generic;
   `Tube` is cheap to keep and useful for the test case. No CAD kernel
   (ADR-013).
3. **Wire:** the XML `<Wire>` element is the cell entry (number + position);
   there is no separate object, radius, material or Geant4 volume (ADR-019).
4. **pyg4ometry:** optional extra `mplDTs[g4]`, deferred. The seam is
   `VolumeSink`; no core dependency (ADR-014).
5. **Output:** `.tg` first (already works and is easy to read), GDML later via
   the pyg4ometry backend. Both are `VolumeSink`s (ADR-015).

**Resolved in revision 4 (defaults; change requires an ADR):**

- compatibility horizon: until 3.0;
- plotting: orientation-based phi/eta, `faceview` kept;
- event scope: Segment/Track/Jet only; no hits/digis;
- yoke: stays in the simulator until Phase 6;
- CLI/YAML: out of scope;
- Phase 0: six tickets (T-004 folded into T-003).

## 14. Physical volumes, honeycomb and yoke

The policy is intentionally narrow and explicit:

| Object | Physical? | Where it lives |
|---|---|---|
| Station (air envelope) | yes | `StationSpec.shape`, `material="G4_AIR"` |
| Drift cell (gas) | yes | `CellGrid`/`CellSpec.shape`, gas material |
| Honeycomb (aluminium) | yes | station attachment (`SolidSpec`) |
| Yoke (iron, with station holes) | yes | detector `StructureSpec`, CSG payload |
| Super layer / layer | no | grouping frames (`shape=None`) |

**Honeycomb.** It is a passive box between SL2 and SL1 (or SL3 for MB4). The
clean representation is a station attachment:

```python
@dataclass
class SolidSpec:
    name: str
    pose: Pose
    shape: Shape
    material: str

StationSpec.attachments: list[SolidSpec] = []
```

The CMS preset computes the gap from the SL poses and adds the attachment; the
core only sees a child solid. `VolumeSink` must emit it like any other node.

**Yoke.** It is a detector-level iron structure with station-shaped holes. The
core must **not** implement CSG. The spec can carry the data
(`StructureSpec.shape`, `subtractions=[(Shape, Pose)]`, material), and a
CSG-capable backend (pyg4ometry) builds it. Until then, the yoke stays in
`DTG4Simulator`; the hook exists so the data model does not have to change
later.

**Consequences.** The exporter has four kinds of solids: station, cell,
attachment (honeycomb) and structure (yoke). There is no separate wire object
to export. A backend that cannot do CSG can reject the yoke structure
explicitly, while still exporting stations/cells/honeycomb.

---

## 15. Beyond geometry: segments, tracks and jets

`mplDTs` already has `Segment`, `Segments`, `AMDTSegment` and `AMDTSegments`.
They are **event-level annotations**, not detector solids: they describe a
particle path or a trigger primitive in a frame, and they must not enter the
Geant4 geometry.

The right structure is a second layer that reuses the geometry's frames:

```
mpldts/
  geometry/     detector: nodes, shapes, materials, poses, FrameGraph
  events/       per-event annotations: Segment, Track, Jet, Hit
  patches/      renderers for both
```

**Common annotation model**

- `Annotation`: a frame reference (`Station`, `SL2`, a cell, or `CMS`), an
  optional style, and an attribute bag (time, charge, pT, pdgId, ...).
- `Segment`: a straight line, either two endpoints or
  centre + direction + length. The current `AMDTSegment` is a constructor of
  this type.
- `Track`: an ordered polyline (`N×3` points) plus per-point attributes
  (time, energy loss); a muon track is the canonical case.
- `Jet` / `Cone`: apex + axis + opening angle (or two angles) plus pT/energy;
  a visual cone, not a solid.
- `Hit` / `Digi` (optional): a point/cell reference with attributes.

**Collections.** A generic `AnnotationCollection` with iteration, indexing,
`filter`, `groupby`, `to_dataframe`; `Segments`, `Tracks`, `Jets` are thin
subclasses. Keep the existing `Segments.groupby` and `AMDTSegments` behaviour.

**Transforms.** Every annotation uses the same `FrameGraph`/`FrameView` as the
geometry. A segment's `local_center`/`global_center` are derived, never stored
twice. Tracks are usually stored in `CMS`; segments usually in a station frame.
No new transform code is needed.

**Difficulty and risks.** Low-to-moderate: the transform infrastructure is the
hard part and already exists. The work is data modelling, collection semantics
and 2D projections (a cone becomes a wedge in phi/eta; a track becomes a
polyline). The risks are scope creep (do not build a full event data model) and
coupling annotations to the immutable detector. Keep attributes as an opaque
bag and keep event serialization separate (`mpldts.event/1`).

**Order.** Phase 4 is optional, after the geometry core (Phase 2). It does not block the
geometry refactor and can run in parallel with assemblies/authoring.

---

## 16. `.tg` first, GDML later

`DTG4Simulator` already reads `.tg` with `G4tgbVolumeMgr`, and the format is easy
to inspect. Keep it as the first exporter:

1. Implement `TgSink(VolumeSink)` in Phase 5; it emits `:SOLID`, `:VOLU`,
   `:PLACEm` and rotations from the same placements.
2. Validate against the current generator for one station; then switch the
   generator to the spec path.
3. Add GDML later through the optional pyg4ometry backend (Phase 6). Both
   backends consume the same `VolumeSink`; no model change.

The yoke needs boolean subtraction, which the `.tg` path already builds with
`UNION`/`SUBTRACTION`. Keep that logic in the simulator or in a CSG-aware sink
until the pyg4ometry backend can take it over.

---

## 17. GitHub workflow and tickets

- **Ticket** is the unit of work. `T-0xx`, one file in `.agents/tickets/`,
  status in `TICKETS.md`, checkpoint in `PROGRESS.md`.
- **Branch** from `main`: `feature/T-0xx-<slug>`.
- **Commits**: `T-0xx: <imperative summary>`, small and reviewable.
- **PR**: uses `.github/pull_request_template.md`, links the ticket, lists
  tests and the oracle result, and states compatibility impact.
- **Review**: at least one approval; CI must be green. The maintainer merges.
- **Milestones**: tag `geometry-refactor-M0` … `M5`; no version bump until the
  public API is stable.
- **Baseline**: first reconcile the current `enhancement-cacheObjects` branch
  with `main` (T-007), then branch the refactor from `main`.

## Appendix A — Current → target mapping

| Today | Target |
|---|---|
| `DTGEOMETRY.get("LocalPosition", rawId=...)` | `node.pose.translation` (parent-relative) |
| `DTGEOMETRY.get("GlobalPosition", ...)` | derived `world_pose.translation`; XML value kept for the oracle |
| `bounds = (width, height, length)` | `shape.dimensions`; `shape.aabb()` for AABB |
| `Station(wheel, sector, station)` | compatibility wrapper → `CMSXMLSource` + `build_station` |
| `SuperLayer(rawId)` / `Layer(rawId)` / `DriftCell(number)` | `from_spec(...)` + legacy wrappers |
| `<Wire>` XML element | cell entry → `CellGrid`; there is no separate wire object |
| station/cell/honeycomb/yoke | physical nodes/attachments/structures; SL/layer grouping |
| `Segment`/`Segments` | Phase 4 annotation layer; backward-compatible |
| tracks / jets | Phase 4 annotations (`Track` polyline, `Jet` cone); not solids |
| `if number == 2: Rz(90°)` | SL2 spec has a rotated pose |
| `face_orientation_factor`, `SectorRef`, `SL13Center` | `presets/cms.py` + virtual frames |
| per-cell `TransformManager` | `Pose` tree + shared `FrameGraph` |
| `StationsCache` + `set_cell_attrs` | immutable specs/stations + event overlay |
| `.tg` generator knows CMS | generic spec walk + `VolumeSink` backend (`pyg4ometry`/GDML later) |

## Appendix B — Measured facts

- XML: 20.8 MB, 250 chambers, 61,760 layers, 171,732 cell centres.
- Checkout (indexed): `Station(-2,1,2)` 1.00 s; `Station(2,14,4)` 0.71 s;
  `Station(0,1,1)` 0.87 s; geometry import + parse/index ~3.4 s.
- Installed 2.2.0-beta: 1.25 / 2.26 / 1.66 s for the same three chambers.
- The old profile (3.75 s `ElementTree.find`, 2.64 s `get_transformation`)
  belongs to the pre-index code and is retired.
- SL2 error: 2.475 cm (W−2/S1/MB2), 0.424 cm (W0/S5/MB3), 0.707 cm
  (W−2/S2/MB1) = `√2 · |SL_local_x|`.
- CMS stagger: L1 49 cells at x=−102.4; L2 50 at −104.5; L3 49 at −102.4;
  L4 48 starting at id 2, x=−100.3; pitch 4.2 cm.

Reproduce the SL2 diagnosis:

```bash
source env/bin/activate
PYTHONPATH=/home/destrada/mplDTs python - <<'PY'
import numpy as np
from mpldts.geometry import Station
st = Station(-2, 1, 2)
for sl in st.super_layers:
    errs = [np.linalg.norm(c.transformer.transform((0, 0, 0), "Cell", "CMS")
                           - np.array(c.global_center))
            for l in sl.layers for c in l.cells]
    print(sl.number, min(errs), max(errs))
PY
```
