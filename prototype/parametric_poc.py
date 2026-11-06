"""
Proof of concept v2: a parametric, XML-free DT geometry model.

This is intentionally standalone (numpy only).  It does not import or modify
``mpldts``; it de-risks the migration described in
``docs/design/generalization-plan.md``.

Concepts kept deliberately separate (v1 conflated them):

* **Node / topology** - station -> super layer -> layer -> cell.  A node may or
  may not own a solid.  Nodes without a solid are pure grouping frames (the
  current CMS SL/layer grouping).
* **Shape / solid** - ``Box`` or ``Tube`` (extensible).  A cell is the drift
  volume; the XML ``<Wire>`` element is its entry (number + position), not a
  separate object.
* **CellGrid** - how cells repeat in a layer (pitch, count, stagger, first id).
  CMS really does alternate 49/50 cells and shift alternate layers by half a
  pitch, so this is a first-class feature, not a special case.

Transforms:

* every node stores one ``Pose`` (rotation + translation) relative to its
  parent, ``p_parent = R @ p_child + t``;
* the builder composes ``world_pose`` top-down once (fast, no BFS per cell);
* a shared ``FrameGraph`` provides the named-frame point transformations the
  current ``transformer`` API offers (``Cell -> Station -> CMS``), including
  aliases and virtual frames, with cached path composition.

Run:
    python prototype/parametric_poc.py
    python prototype/parametric_poc.py --plot prototype/custom_station.png
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Iterable, Protocol, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# 1. Poses
# ---------------------------------------------------------------------------

def _rot(rotation: Sequence[float]) -> np.ndarray:
    return np.asarray(rotation, dtype=float).reshape(3, 3)


@dataclass(frozen=True)
class Pose:
    """Rigid transform from a child frame to its parent frame.

    ``p_parent = rotation @ p_child + translation``.
    """

    rotation: tuple[float, ...] = (1, 0, 0, 0, 1, 0, 0, 0, 1)
    translation: tuple[float, float, float] = (0.0, 0.0, 0.0)

    @classmethod
    def identity(cls) -> "Pose":
        return cls()

    @classmethod
    def translated(cls, x: float, y: float, z: float) -> "Pose":
        return cls(translation=(float(x), float(y), float(z)))

    @classmethod
    def rotated_x(cls, degrees: float, translation=(0.0, 0.0, 0.0)) -> "Pose":
        a = math.radians(degrees)
        c, s = math.cos(a), math.sin(a)
        return cls(rotation=(1, 0, 0, 0, c, -s, 0, s, c),
                   translation=tuple(float(v) for v in translation))

    @classmethod
    def rotated_y(cls, degrees: float, translation=(0.0, 0.0, 0.0)) -> "Pose":
        a = math.radians(degrees)
        c, s = math.cos(a), math.sin(a)
        return cls(rotation=(c, 0, s, 0, 1, 0, -s, 0, c),
                   translation=tuple(float(v) for v in translation))

    @classmethod
    def rotated_z(cls, degrees: float, translation=(0.0, 0.0, 0.0)) -> "Pose":
        a = math.radians(degrees)
        c, s = math.cos(a), math.sin(a)
        return cls(rotation=(c, -s, 0, s, c, 0, 0, 0, 1),
                   translation=tuple(float(v) for v in translation))

    @property
    def matrix(self) -> np.ndarray:
        m = np.eye(4)
        m[:3, :3] = _rot(self.rotation)
        m[:3, 3] = np.asarray(self.translation, dtype=float)
        return m

    def compose(self, child: "Pose") -> "Pose":
        """Return ``self @ child`` (child expressed in this frame)."""
        m = self.matrix @ child.matrix
        return Pose(rotation=tuple(m[:3, :3].ravel()), translation=tuple(m[:3, 3]))

    def inverse(self) -> "Pose":
        m = np.linalg.inv(self.matrix)
        return Pose(rotation=tuple(m[:3, :3].ravel()), translation=tuple(m[:3, 3]))

    def transform(self, points, kind: str = "point") -> np.ndarray:
        pts = np.atleast_2d(np.asarray(points, dtype=float))
        out = pts @ _rot(self.rotation).T
        if kind == "point":
            out = out + np.asarray(self.translation, dtype=float)
        return out

    def axis(self, index: int) -> np.ndarray:
        return _rot(self.rotation)[:, index]


# ---------------------------------------------------------------------------
# 2. Shapes (solids)
# ---------------------------------------------------------------------------

class Shape:
    """Base class for a primitive solid expressed in the node's local frame."""

    def aabb(self) -> tuple[float, float, float]:
        raise NotImplementedError

    def volume(self) -> float:
        raise NotImplementedError

    def symmetry_axis(self) -> str | None:
        """Local axis of rotational symmetry, if any (backend-neutral)."""
        return None


@dataclass(frozen=True)
class Box(Shape):
    """Full extents along the local x, y, z axes."""

    dx: float
    dy: float
    dz: float

    def aabb(self):
        return (self.dx, self.dy, self.dz)

    def volume(self):
        return self.dx * self.dy * self.dz


@dataclass(frozen=True)
class Tube(Shape):
    """Cylindrical shell with its symmetry axis along ``axis``.

    ``radius`` is the outer radius; ``inner_radius=0`` gives a solid cylinder.
    This is the "cell is a tube, not a box" case.
    """

    radius: float
    length: float
    axis: str = "y"
    inner_radius: float = 0.0

    def aabb(self):
        d = 2.0 * self.radius
        if self.axis == "x":
            return (self.length, d, d)
        if self.axis == "y":
            return (d, self.length, d)
        return (d, d, self.length)

    def volume(self):
        return math.pi * (self.radius ** 2 - self.inner_radius ** 2) * self.length

    def symmetry_axis(self) -> str | None:
        return self.axis



@dataclass
class CellGrid:
    """Regular one-dimensional repetition of cells in a layer.

    ``offset`` encodes the half-cell stagger between adjacent layers
    (CMS uses pitch/2), and ``first_id`` handles the 49/50-cell pattern.
    """

    pitch: float
    count: int
    shape: Shape
    first_id: int = 1
    offset: float = 0.0

    def x_positions(self) -> np.ndarray:
        i = np.arange(self.count, dtype=float)
        return self.offset + (i - (self.count - 1) / 2.0) * self.pitch


# ---------------------------------------------------------------------------
# 3. Declarative description
# ---------------------------------------------------------------------------

@dataclass
class LayerSpec:
    number: int
    pose: Pose
    cells: CellGrid | list[tuple[int, Pose, Shape]]
    shape: Shape | None = None
    material: str | None = None


@dataclass
class SuperLayerSpec:
    number: int
    pose: Pose
    layers: list[LayerSpec] = field(default_factory=list)
    shape: Shape | None = None
    material: str | None = None


@dataclass
class StationSpec:
    name: str
    pose: Pose
    super_layers: list[SuperLayerSpec] = field(default_factory=list)
    shape: Shape | None = None
    material: str = "G4_AIR"
    metadata: dict = field(default_factory=dict)


@dataclass
class DetectorSpec:
    name: str
    pose: Pose
    stations: list[StationSpec] = field(default_factory=list)
    shape: Shape | None = None
    material: str = "G4_Galactic"


# ---------------------------------------------------------------------------
# 4. Runtime topology + shared frame graph
# ---------------------------------------------------------------------------

@dataclass
class Node:
    name: str = ""
    kind: str = "node"
    pose: Pose = field(default_factory=Pose.identity)
    world_pose: Pose = field(default_factory=Pose.identity)
    shape: Shape | None = None
    material: str | None = None
    parent: "Node | None" = None
    frame_id: str = ""
    number: int | None = None
    children: list["Node"] = field(default_factory=list)

    @property
    def center(self) -> tuple[float, float, float]:
        return tuple(float(v) for v in self.world_pose.translation)

    @property
    def bounds(self):
        return self.shape.aabb() if self.shape is not None else None

    @property
    def transformer(self) -> "FrameView":
        return FrameView(self._graph, self)

    def iter_descendants(self) -> Iterable["Node"]:
        for child in self.children:
            yield child
            yield from child.iter_descendants()


@dataclass
class Station(Node):
    super_layers: list["SuperLayer"] = field(default_factory=list)

    def super_layer(self, number: int):
        return next((sl for sl in self.super_layers if sl.number == number), None)

    def cells(self):
        for sl in self.super_layers:
            for layer in sl.layers:
                yield from layer.cells


@dataclass
class SuperLayer(Node):
    layers: list["Layer"] = field(default_factory=list)

    def layer(self, number: int):
        return next((layer for layer in self.layers if layer.number == number), None)


@dataclass
class Layer(Node):
    cells: list["Cell"] = field(default_factory=list)

    def cell(self, number: int):
        return next((c for c in self.cells if c.number == number), None)


@dataclass
class Cell(Node):
    pass


class FrameGraph:
    """Shared named-frame graph: one edge per parent/child pose.

    This is the successor of ``TransformManager``.  The builder needs the pose
    tree only; the graph exists for ad-hoc queries such as
    ``cell.transformer.transform(p, "Cell", "CMS")`` or the CMS-specific
    virtual frames (``StationNvPhi``, ``SL13Center``, ...).
    """

    def __init__(self, root: str = "World"):
        self.root = root
        self._adj: dict[str, list[tuple[str, Pose]]] = {root: []}
        self._virtuals: dict[str, str] = {}
        self._cache: dict[tuple[str, str], Pose] = {}

    def add_edge(self, child: str, parent: str, pose_child_in_parent: Pose) -> None:
        self._adj.setdefault(child, []).append((parent, pose_child_in_parent))
        self._adj.setdefault(parent, []).append((child, pose_child_in_parent.inverse()))
        self._cache.clear()

    def add_virtual(self, name: str, relative_to: str, pose: Pose) -> None:
        """Register a frame that is not a geometry node (e.g. SL13Center)."""
        self.add_edge(name, relative_to, pose)
        self._virtuals[name] = relative_to

    def matrix(self, from_frame: str, to_frame: str) -> Pose:
        key = (from_frame, to_frame)
        if key in self._cache:
            return self._cache[key]
        if from_frame == to_frame:
            return Pose.identity()

        # BFS; acc maps coordinates in ``from_frame`` to the current frame.
        from collections import deque

        queue = deque([(from_frame, Pose.identity())])
        seen = {from_frame}
        while queue:
            current, acc = queue.popleft()
            for other, current_to_other in self._adj.get(current, []):
                if other in seen:
                    continue
                new_acc = current_to_other.compose(acc)
                if other == to_frame:
                    self._cache[key] = new_acc
                    return new_acc
                seen.add(other)
                queue.append((other, new_acc))
        raise KeyError(f"no frame path from {from_frame!r} to {to_frame!r}")

    def transform(self, points, from_frame: str, to_frame: str, kind: str = "point"):
        arr = np.asarray(points, dtype=float)
        single = arr.ndim == 1
        out = self.matrix(from_frame, to_frame).transform(arr, kind=kind)
        return out[0] if single else out


class FrameView:
    """Per-object view of the shared graph (backward-compatible ``transformer``).

    Aliases are resolved in the object's scope, which keeps names such as
    ``"Cell"``, ``"Layer"``, ``"Station"`` unambiguous even though the full
    frame ids are unique paths.
    """

    def __init__(self, graph: FrameGraph, node: Node):
        self.graph = graph
        self.node = node
        self.aliases = self._build_aliases(graph, node)

    @staticmethod
    def _build_aliases(graph: FrameGraph, node: Node) -> dict[str, str]:
        aliases = {"World": graph.root, "CMS": graph.root, "This": node.frame_id}
        cur: Node | None = node
        while cur is not None:
            if cur.kind == "station":
                aliases["Station"] = cur.frame_id
            elif cur.kind == "superlayer":
                aliases["SuperLayer"] = cur.frame_id
                aliases[f"SL{cur.number}"] = cur.frame_id
            elif cur.kind == "layer":
                aliases["Layer"] = cur.frame_id
            elif cur.kind == "cell":
                aliases["Cell"] = cur.frame_id
            cur = cur.parent
        # a station view can also address its super layers by number
        if node.kind == "station":
            for child in node.children:
                if child.kind == "superlayer":
                    aliases[f"SL{child.number}"] = child.frame_id
        aliases.update({name: name for name in graph._virtuals})
        return aliases

    def _resolve(self, name: str) -> str:
        if name in self.aliases:
            return self.aliases[name]
        if name in self.graph._adj:
            return name
        raise KeyError(f"frame {name!r} is not available in this scope: {sorted(self.aliases)}")

    @property
    def available_frames(self) -> set[str]:
        return set(self.aliases)

    def get_transformation(self, from_frame: str, to_frame: str) -> np.ndarray:
        return self.graph.matrix(self._resolve(from_frame), self._resolve(to_frame)).matrix

    def transform(self, P, from_frame: str, to_frame: str, type: str = "point"):
        kind = "vector" if type == "vector" else "point"
        return self.graph.transform(
            P, self._resolve(from_frame), self._resolve(to_frame), kind=kind
        )


# ---------------------------------------------------------------------------
# 5. Builder
# ---------------------------------------------------------------------------

def _grid_cells(grid: CellGrid):
    for i, x in enumerate(grid.x_positions()):
        number = grid.first_id + i
        yield number, Pose.translated(x, 0.0, 0.0), grid.shape


def build_station(spec: StationSpec, graph: FrameGraph, parent: Node | None = None,
                  parent_pose: Pose | None = None, parent_frame: str | None = None) -> Station:
    parent_pose = parent_pose or Pose.identity()
    parent_frame = parent_frame or (parent.frame_id if parent is not None else graph.root)
    world_pose = parent_pose.compose(spec.pose)
    frame_id = f"{parent_frame}/{spec.name}"

    station = Station(
        name=spec.name, kind="station", pose=spec.pose, world_pose=world_pose,
        shape=spec.shape, material=spec.material, parent=parent,
        frame_id=frame_id, children=[],
    )
    station._graph = graph
    graph.add_edge(frame_id, parent_frame, spec.pose)
    if parent is not None:
        parent.children.append(station)

    for sl_spec in spec.super_layers:
        sl_pose = world_pose.compose(sl_spec.pose)
        sl = SuperLayer(
            name=f"SL{sl_spec.number}", kind="superlayer", pose=sl_spec.pose,
            world_pose=sl_pose, shape=sl_spec.shape, material=sl_spec.material,
            parent=station, frame_id=f"{frame_id}/SL{sl_spec.number}", number=sl_spec.number,
        )
        sl._graph = graph
        graph.add_edge(sl.frame_id, frame_id, sl_spec.pose)
        station.children.append(sl)
        station.super_layers.append(sl)

        for layer_spec in sl_spec.layers:
            layer_pose = sl_pose.compose(layer_spec.pose)
            layer = Layer(
                name=f"L{layer_spec.number}", kind="layer", pose=layer_spec.pose,
                world_pose=layer_pose, shape=layer_spec.shape,
                material=layer_spec.material, parent=sl,
                frame_id=f"{sl.frame_id}/L{layer_spec.number}", number=layer_spec.number,
            )
            layer._graph = graph
            graph.add_edge(layer.frame_id, sl.frame_id, layer_spec.pose)
            sl.children.append(layer)
            sl.layers.append(layer)

            if isinstance(layer_spec.cells, CellGrid):
                cell_specs = list(_grid_cells(layer_spec.cells))
            else:
                cell_specs = layer_spec.cells
            for number, cell_pose, shape in cell_specs:
                cell = Cell(
                    name=f"C{number}", kind="cell", pose=cell_pose,
                    world_pose=layer_pose.compose(cell_pose), shape=shape,
                    material=None, parent=layer,
                    frame_id=f"{layer.frame_id}/C{number}", number=number,
                )
                cell._graph = graph
                graph.add_edge(cell.frame_id, layer.frame_id, cell_pose)
                layer.children.append(cell)
                layer.cells.append(cell)

    return station


# ---------------------------------------------------------------------------
# 6. Backend-agnostic export seam
# ---------------------------------------------------------------------------
#
# The core never imports a backend.  A future pyg4ometry bridge, a .tg writer
# or GDML writer implements ``VolumeSink`` and receives already-folded
# placements.  This is the only contract the bridge needs; see
# docs/design/generalization-plan.md section 8.

@dataclass
class VolumePlacement:
    node: Node
    mother: Node | None
    pose_in_mother: Pose  # grouping nodes folded in


class VolumeSink(Protocol):
    """Minimal sink implemented by any exporter backend."""

    def begin(self, root: Node) -> None: ...
    def place(self, node: Node, mother: Node | None, pose_in_mother: Pose) -> None: ...
    def end(self) -> None: ...


@dataclass
class RecordingSink:
    """Dependency-free sink used by tests and by the demo."""

    placements: list[VolumePlacement] = field(default_factory=list)
    begun: bool = False
    ended: bool = False
    root: Node | None = None

    def begin(self, root: Node) -> None:
        self.root = root
        self.begun = True

    def place(self, node: Node, mother: Node | None, pose_in_mother: Pose) -> None:
        self.placements.append(VolumePlacement(node, mother, pose_in_mother))

    def end(self) -> None:
        self.ended = True


def export_volumes(root: Node, sink: VolumeSink) -> None:
    """Drive any backend from the placement walk."""
    sink.begin(root)
    for placement in iter_volume_placements(root):
        sink.place(placement.node, placement.mother, placement.pose_in_mother)
    sink.end()


def g4_alignment(shape: Shape) -> Pose:
    """Adapter used by a Geant4/pyg4ometry backend (kept out of ``Shape``).

    Geant4 ``Tubs`` is built along +z, so a tube whose symmetry axis is y needs
    a z->y rotation.  A different backend can implement its own mapping; the
    spec only exposes ``symmetry_axis()``.
    """
    axis = shape.symmetry_axis()
    if axis == "y":
        return Pose.rotated_x(-90.0)
    if axis == "x":
        return Pose.rotated_y(90.0)
    return Pose.identity()


def iter_volume_placements(root: Node) -> Iterable[VolumePlacement]:
    """Pre-order walk that folds nodes without a solid into the next placement.

    This is the core of every exporter (``.tg``, GDML, pyg4ometry): only nodes
    with a shape become volumes; pure grouping nodes contribute a pose.
    """

    def walk(node: Node, mother: Node | None, pose_in_mother: Pose):
        if node.shape is not None:
            yield VolumePlacement(node, mother, pose_in_mother)
            mother = node
            pose_in_mother = Pose.identity()
        for child in node.children:
            yield from walk(child, mother, pose_in_mother.compose(child.pose))

    yield from walk(root, None, root.pose)


# ---------------------------------------------------------------------------
# 7. Serialization
# ---------------------------------------------------------------------------

def _pose_to_dict(p: Pose) -> dict:
    return {"rotation": list(p.rotation), "translation": list(p.translation)}


def _pose_from_dict(d: dict) -> Pose:
    return Pose(rotation=tuple(d["rotation"]), translation=tuple(d["translation"]))


def _shape_to_dict(s: Shape) -> dict:
    if isinstance(s, Box):
        return {"kind": "box", "dx": s.dx, "dy": s.dy, "dz": s.dz}
    if isinstance(s, Tube):
        return {"kind": "tube", "radius": s.radius, "length": s.length,
                "axis": s.axis, "inner_radius": s.inner_radius}
    raise TypeError(f"unsupported shape {s!r}")


def _shape_from_dict(d: dict) -> Shape:
    if d["kind"] == "box":
        return Box(d["dx"], d["dy"], d["dz"])
    if d["kind"] == "tube":
        return Tube(d["radius"], d["length"], d["axis"], d.get("inner_radius", 0.0))
    raise ValueError(f"unknown shape kind {d['kind']!r}")


def station_to_dict(spec: StationSpec) -> dict:
    def grid_to_dict(g: CellGrid) -> dict:
        return {"pitch": g.pitch, "count": g.count, "shape": _shape_to_dict(g.shape),
                "first_id": g.first_id, "offset": g.offset}

    return {
        "schema": "mpldts.station/2",
        "name": spec.name,
        "pose": _pose_to_dict(spec.pose),
        "shape": _shape_to_dict(spec.shape) if spec.shape else None,
        "material": spec.material,
        "metadata": spec.metadata,
        "super_layers": [
            {
                "number": sl.number,
                "pose": _pose_to_dict(sl.pose),
                "shape": _shape_to_dict(sl.shape) if sl.shape else None,
                "material": sl.material,
                "layers": [
                    {
                        "number": layer.number,
                        "pose": _pose_to_dict(layer.pose),
                        "shape": _shape_to_dict(layer.shape) if layer.shape else None,
                        "material": layer.material,
                        "grid": grid_to_dict(layer.cells)
                        if isinstance(layer.cells, CellGrid) else None,
                    }
                    for layer in sl.layers
                ],
            }
            for sl in spec.super_layers
        ],
    }


def station_from_dict(d: dict) -> StationSpec:
    def grid_from_dict(g: dict) -> CellGrid:
        return CellGrid(
            pitch=g["pitch"], count=g["count"], shape=_shape_from_dict(g["shape"]),
            first_id=g["first_id"], offset=g["offset"],
        )

    return StationSpec(
        name=d["name"],
        pose=_pose_from_dict(d["pose"]),
        shape=_shape_from_dict(d["shape"]) if d["shape"] else None,
        material=d["material"],
        metadata=d.get("metadata", {}),
        super_layers=[
            SuperLayerSpec(
                number=sl["number"], pose=_pose_from_dict(sl["pose"]),
                shape=_shape_from_dict(sl["shape"]) if sl["shape"] else None,
                material=sl["material"],
                layers=[
                    LayerSpec(
                        number=layer["number"], pose=_pose_from_dict(layer["pose"]),
                        shape=_shape_from_dict(layer["shape"]) if layer["shape"] else None,
                        material=layer["material"],
                        cells=grid_from_dict(layer["grid"]),
                    )
                    for layer in sl["layers"]
                ],
            )
            for sl in d["super_layers"]
        ],
    )


# ---------------------------------------------------------------------------
# 8. Example descriptions
# ---------------------------------------------------------------------------

def make_box_station(name: str = "box-station", n_cells: int = 24) -> StationSpec:
    """CMS-like station: staggered layers, 49/50-cell pattern, box cells."""
    pitch, length = 4.2, 100.0
    width = (n_cells + 1) * pitch + 2.0

    # CMS pattern: 49/50/49/48 cells, half-cell stagger, L4 starts at id 2.
    counts = [n_cells, n_cells + 1, n_cells, n_cells - 1]
    offsets = [0.0, -pitch / 2.0, 0.0, +pitch / 2.0]
    first_ids = [1, 1, 1, 2]
    layers = []
    for i in range(4):
        layers.append(
            LayerSpec(
                number=i + 1,
                pose=Pose.translated(0.0, 0.0, -1.95 + 1.3 * i),
                shape=None,
                cells=CellGrid(
                    pitch=pitch, count=counts[i], first_id=first_ids[i],
                    offset=offsets[i], shape=Box(pitch, length, 1.3),
                ),
            )
        )

    def sl(number: int, z: float, rotated: bool) -> SuperLayerSpec:
        return SuperLayerSpec(
            number=number,
            pose=Pose.rotated_z(90.0 if rotated else 0.0, translation=(0.0, 0.0, z)),
            layers=layers,
        )

    return StationSpec(
        name=name,
        pose=Pose.identity(),
        shape=Box(width + 6.0, length + 10.0, 40.0),
        super_layers=[sl(1, +8.0, False), sl(2, -8.0, True)],
        metadata={"kind": "box-demo", "units": "cm"},
    )


def make_tube_station(name: str = "tube-station", n_cells: int = 16) -> StationSpec:
    """A drift-cell station made of cylindrical cells (circles, not boxes)."""
    pitch, length, radius = 5.0, 100.0, 2.2
    width = (n_cells + 1) * pitch + 2.0

    layers = [
        LayerSpec(
            number=i + 1,
            pose=Pose.translated(0.0, 0.0, -1.95 + 1.3 * i),
            shape=None,
            cells=CellGrid(
                pitch=pitch, count=n_cells,
                offset=0.0 if i % 2 == 0 else -pitch / 2.0,
                shape=Tube(radius=radius, length=length, axis="y"),
            ),
        )
        for i in range(4)
    ]
    return StationSpec(
        name=name,
        pose=Pose.rotated_z(25.0, translation=(260.0, 0.0, 0.0)),
        shape=Box(width + 6.0, length + 10.0, 40.0),
        super_layers=[SuperLayerSpec(number=1, pose=Pose.translated(0, 0, 8), layers=layers)],
        metadata={"kind": "tube-demo", "units": "cm"},
    )


# ---------------------------------------------------------------------------
# 9. Validation and demo
# ---------------------------------------------------------------------------

def validate(spec: StationSpec) -> list[str]:
    problems = []
    if spec.shape is not None and any(v <= 0 for v in spec.shape.aabb()):
        problems.append(f"{spec.name}: non-positive station size")
    for sl in spec.super_layers:
        for layer in sl.layers:
            if not isinstance(layer.cells, CellGrid):
                continue
            grid = layer.cells
            used = grid.count * grid.pitch
            if used <= 0:
                problems.append(f"{spec.name}/SL{sl.number}/L{layer.number}: empty grid")
            if layer.shape is not None and used > layer.shape.aabb()[0] + 1e-6:
                problems.append(f"{spec.name}/SL{sl.number}/L{layer.number}: cells wider than layer")
    if not problems:
        print(f"[validate] {spec.name}: OK")
    return problems


def independent_center(station: Station, cell: Cell) -> np.ndarray:
    """Recompute a cell centre from the spec path with raw 4x4 matrices."""
    sl = cell.parent.parent
    layer = cell.parent
    return (
        station.world_pose.matrix
        @ sl.pose.matrix
        @ layer.pose.matrix
        @ cell.pose.matrix
    )[:3, 3]


def demo(plot_path: str | None = None) -> None:
    graph = FrameGraph("World")
    box_spec = make_box_station()
    tube_spec = make_tube_station()
    for spec in (box_spec, tube_spec):
        problems = validate(spec)
        if problems:
            raise SystemExit("validation failed:\n" + "\n".join(problems))

    box_station = build_station(box_spec, graph)
    tube_station = build_station(tube_spec, graph)

    # -- 1. builder vs independent matrix product -------------------------
    max_err = 0.0
    for station in (box_station, tube_station):
        for cell in station.cells():
            expected = independent_center(station, cell)
            max_err = max(max_err, float(np.linalg.norm(np.asarray(cell.center) - expected)))
    print(f"[check] max |builder - independent 4x4| = {max_err:.3e} cm")
    assert max_err < 1e-9

    # -- 2. frame graph: full path, aliases, inverse, vectors -------------
    cell = box_station.super_layer(1).layer(2).cell(5)
    full = graph.transform((0, 0, 0), cell.frame_id, graph.root)
    alias = cell.transformer.transform((0, 0, 0), "Cell", "World")
    back = cell.transformer.transform(cell.center, "World", "Cell")
    vec = cell.transformer.transform((1, 0, 0), "Cell", "World", type="vector")
    cms = cell.transformer.transform((0, 0, 0), "Cell", "CMS")
    print(f"[check] graph full path vs alias      = {np.linalg.norm(full - alias):.3e} cm")
    print(f"[check] Cell -> CMS (legacy alias)    = {np.linalg.norm(cms - np.asarray(cell.center)):.3e} cm")
    print(f"[check] World -> Cell round-trip      = {np.linalg.norm(back):.3e} cm")
    print(f"[check] vector vs pose axis           = {np.linalg.norm(vec - cell.world_pose.axis(0)):.3e}")
    assert np.linalg.norm(full - alias) < 1e-12
    assert np.linalg.norm(cms - np.asarray(cell.center)) < 1e-9
    assert np.linalg.norm(back) < 1e-9
    assert np.linalg.norm(vec - cell.world_pose.axis(0)) < 1e-12

    # -- 3. virtual frame (CMS-style StationNvPhi) ------------------------
    graph.add_virtual("StationNvPhi", box_station.frame_id, Pose.rotated_z(180.0))
    nv = box_station.transformer.get_transformation("StationNvPhi", "Station")
    print(f"[check] virtual StationNvPhi rotation  =\n{np.round(nv[:3, :3], 3)}")

    # -- 4. JSON round-trip ------------------------------------------------
    payload = json.dumps(station_to_dict(box_spec), indent=2)
    rebuilt_spec = station_from_dict(json.loads(payload))
    rebuilt = build_station(rebuilt_spec, FrameGraph("World"))
    rt_err = max(
        float(np.linalg.norm(np.asarray(a.center) - np.asarray(b.center)))
        for a, b in zip(box_station.cells(), rebuilt.cells())
    )
    print(f"[check] JSON round-trip max error      = {rt_err:.3e} cm")
    assert rt_err < 1e-9

    # -- 5. exporter planning ---------------------------------------------
    placements = list(iter_volume_placements(box_station))
    print(f"[g4] volumes in box station: {len(placements)} "
          f"(1 station + {sum(1 for p in placements if p.node.kind == 'cell')} cells)")
    for pl in placements[:3]:
        mother = pl.mother.name if pl.mother else "World"
        print(f"      {pl.node.name:<10} in {mother:<10} "
              f"at {np.round(pl.pose_in_mother.translation, 2)}")
    # every cell placement, folded through grouping nodes, must land on its centre
    g4_err = 0.0
    for pl in placements:
        if pl.node.kind != "cell":
            continue
        world = (pl.mother.world_pose if pl.mother else Pose.identity()).compose(pl.pose_in_mother)
        g4_err = max(g4_err, float(np.linalg.norm(world.translation - np.asarray(pl.node.center))))
    print(f"[g4] folded placement max error        = {g4_err:.3e} cm")
    assert g4_err < 1e-9

    # -- 5b. backend seam: the only contract a future pyg4ometry bridge needs
    sink = RecordingSink()
    export_volumes(box_station, sink)
    assert sink.begun and sink.ended and len(sink.placements) == len(placements)
    print(f"[backend] VolumeSink received {len(sink.placements)} placements "
          f"(root={sink.root.name}, begun={sink.begun}, ended={sink.ended})")

    box_cell = box_station.super_layer(1).layer(1).cell(1)
    tube_cell = tube_station.super_layer(1).layer(1).cell(1)
    box_align = g4_alignment(box_cell.shape)
    tube_align = g4_alignment(tube_cell.shape)
    assert np.allclose(box_align.rotation, Pose.identity().rotation)
    assert np.allclose(tube_align.rotation, Pose.rotated_x(-90.0).rotation)
    print("[backend] g4 alignment: box=identity, tube=R_x(-90) [z->y]")

    # -- 6. shape sanity --------------------------------------------------
    tube = tube_cell
    print(f"[shapes] box cell volume   = {box_cell.shape.volume():.1f} cm^3")
    print(f"[shapes] tube cell volume  = {tube.shape.volume():.1f} cm^3 "
          f"(r={tube.shape.radius}, L={tube.shape.length})")
    print(f"[shapes] station centres   = {np.round(box_station.center, 1)} | {np.round(tube_station.center, 1)}")

    if plot_path:
        _plot(box_station, tube_station, plot_path)
        print(f"[plot] wrote {plot_path}")


def _poly(center, ex, ey, ez, dx, dy, dz, view):
    """Project a box onto (x,z) for phi or (y,z) for eta."""
    if view == "phi":
        e1, e2, d1, d2 = ex, ez, dx, dz
    else:
        e1, e2, d1, d2 = ey, ez, dy, dz
    corners = [
        center + a * e1 * d1 / 2 + b * e2 * d2 / 2
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))
    ]
    i, j = (0, 2) if view == "phi" else (1, 2)
    return [(float(c[i]), float(c[j])) for c in corners]


def _plot(box_station: Station, tube_station: Station, path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Polygon

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for row, station in enumerate((box_station, tube_station)):
        inv = station.world_pose.inverse()
        for col, view in enumerate(("phi", "eta")):
            ax = axes[row][col]
            ax.set_title(f"{station.name} - {view}")
            ax.set_aspect("equal")
            ax.set_xlabel("station x [cm]" if view == "phi" else "station y [cm]")
            ax.set_ylabel("station z [cm]")

            if station.shape is not None:
                dx, dy, dz = station.shape.aabb()
                ax.add_patch(Polygon(_poly(np.zeros(3), np.eye(3)[:, 0], np.eye(3)[:, 1],
                                           np.eye(3)[:, 2], dx, dy, dz, view),
                                     closed=True, fill=False, lw=1.2, ec="0.4"))

            for cell in station.cells():
                m = inv.matrix @ cell.world_pose.matrix
                c = m[:3, 3]
                ex, ey, ez = m[:3, 0], m[:3, 1], m[:3, 2]
                if isinstance(cell.shape, Tube):
                    if view == "phi":
                        ax.add_patch(Circle((c[0], c[2]), cell.shape.radius, fill=False,
                                            lw=0.5, ec="tab:orange"))
                    else:
                        ax.add_patch(Polygon(
                            _poly(c, ex, ey, ez, 2 * cell.shape.radius,
                                  cell.shape.length, 2 * cell.shape.radius, view),
                            closed=True, fill=False, lw=0.5, ec="tab:orange"))
                else:
                    dx, dy, dz = cell.shape.aabb()
                    ax.add_patch(Polygon(_poly(c, ex, ey, ez, dx, dy, dz, view),
                                         closed=True, fill=False, lw=0.4, ec="tab:blue"))
                if view == "phi":
                    ax.plot([c[0]], [c[2]], marker=".", ms=1.5, color="k")
            ax.autoscale_view()
    fig.tight_layout()
    fig.savefig(path, dpi=140)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", default=None, help="write a PNG preview")
    args = parser.parse_args()
    demo(plot_path=args.plot)
