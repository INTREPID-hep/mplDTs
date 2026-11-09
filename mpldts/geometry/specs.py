"""Immutable geometry specs (T-010).

Declarative description of a DT detector: one pose per node, primitive shapes,
cell grids and the node specs. Units are cm. Every pose is parent-relative:

    p_parent = R * p_child + t

No I/O, no XML, no matplotlib and no backend import: the CMS source (T-011)
and the runtime builder (Phase 2) consume this module.

Specs are frozen dataclasses with eq=False, because Pose and Shape hold numpy
arrays. Compare fields in tests, not instances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

__all__ = [
    "Pose",
    "Shape",
    "Box",
    "Tube",
    "CellGrid",
    "LayerSpec",
    "SuperLayerSpec",
    "StationSpec",
    "AttachmentSpec",
    "StructureSpec",
    "DetectorSpec",
    "validate",
]

#: Max deviation allowed when checking that a rotation is orthonormal.
ROTATION_TOLERANCE = 1e-9


def _as_vector(values, size, name):
    array = np.asarray(values, dtype=float)
    if array.shape != (size,):
        raise ValueError("%s must have shape (%d,), got %s" % (name, size, array.shape))
    return array


@dataclass(frozen=True, eq=False)
class Pose:
    """Rigid transform of a child frame in its parent: p_parent = R * p + t."""

    rotation: np.ndarray = field(default_factory=lambda: np.eye(3))
    translation: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self):
        rotation = np.asarray(self.rotation, dtype=float)
        if rotation.shape != (3, 3):
            raise ValueError("rotation must have shape (3, 3), got %s" % (rotation.shape,))
        object.__setattr__(self, "rotation", rotation)
        object.__setattr__(self, "translation", _as_vector(self.translation, 3, "translation"))

    @classmethod
    def identity(cls):
        return cls()

    @classmethod
    def translated(cls, x, y, z):
        return cls(np.eye(3), (x, y, z))

    @classmethod
    def rotated_z(cls, degrees, translation=(0.0, 0.0, 0.0)):
        angle = np.radians(degrees)
        cos, sin = np.cos(angle), np.sin(angle)
        return cls(
            np.array([[cos, -sin, 0.0], [sin, cos, 0.0], [0.0, 0.0, 1.0]]),
            translation,
        )

    @classmethod
    def from_matrix(cls, matrix):
        matrix = np.asarray(matrix, dtype=float)
        if matrix.shape != (4, 4):
            raise ValueError("matrix must have shape (4, 4), got %s" % (matrix.shape,))
        return cls(matrix[:3, :3], matrix[:3, 3])

    def matrix(self):
        """The 4x4 homogeneous matrix of this pose."""
        matrix = np.eye(4)
        matrix[:3, :3] = self.rotation
        matrix[:3, 3] = self.translation
        return matrix

    def compose(self, child):
        """self after child: p_self = self.rotation * (child(p)) + t."""
        return Pose(
            self.rotation @ child.rotation,
            self.rotation @ child.translation + self.translation,
        )

    def inverse(self):
        rotation = self.rotation.T
        return Pose(rotation, -rotation @ self.translation)

    def apply(self, points, kind="point"):
        """Transform one point/vector (3,) or many (N, 3)."""
        if kind not in ("point", "vector"):
            raise ValueError("kind must be 'point' or 'vector', got %r" % (kind,))
        array = np.asarray(points, dtype=float)
        if array.shape[-1:] != (3,):
            raise ValueError("points must end in 3 coordinates, got %s" % (array.shape,))
        moved = array @ self.rotation.T
        return moved + self.translation if kind == "point" else moved

    def __repr__(self):
        return "Pose(rotation=%s, translation=%s)" % (
            np.array2string(self.rotation, precision=4),
            np.array2string(self.translation, precision=4),
        )


class Shape:
    """A primitive solid. Extents are full lengths in the node local frame."""

    def aabb(self):
        raise NotImplementedError

    def volume(self):
        raise NotImplementedError

    def symmetry_axis(self):
        """Axis the primitive is symmetric about, or None."""
        return None


@dataclass(frozen=True, eq=False)
class Box(Shape):
    """CMS drift cell: dx = pitch, dy = cell length, dz = drift gap."""

    dx: float
    dy: float
    dz: float

    def aabb(self):
        return (float(self.dx), float(self.dy), float(self.dz))

    def volume(self):
        return float(self.dx) * float(self.dy) * float(self.dz)


@dataclass(frozen=True, eq=False)
class Tube(Shape):
    """Cylinder along axis (cell length by default), optionally a shell."""

    radius: float
    length: float
    axis: str = "y"
    inner_radius: float = 0.0

    def aabb(self):
        across = 2.0 * abs(float(self.radius))
        along = abs(float(self.length))
        if self.axis == "x":
            return (along, across, across)
        if self.axis == "y":
            return (across, along, across)
        if self.axis == "z":
            return (across, across, along)
        raise ValueError("axis must be 'x', 'y' or 'z', got %r" % (self.axis,))

    def volume(self):
        outer = float(self.radius) ** 2
        inner = float(self.inner_radius) ** 2
        return float(np.pi) * (outer - inner) * abs(float(self.length))

    def symmetry_axis(self):
        return self.axis


@dataclass(frozen=True, eq=False)
class CellGrid:
    """count equal cells along x, centred on the layer frame."""

    pitch: float
    count: int
    shape: Shape
    first_id: int = 1
    offset: float = 0.0
    material: Optional[str] = None

    def x_positions(self):
        """Cell centres along x, in the layer frame."""
        index = np.arange(self.count, dtype=float)
        return self.offset + (index - (self.count - 1) / 2.0) * float(self.pitch)

    def ids(self):
        return list(range(self.first_id, self.first_id + self.count))


@dataclass(frozen=True, eq=False)
class LayerSpec:
    number: int
    pose: Pose
    cells: CellGrid
    shape: Optional[Shape] = None
    material: Optional[str] = None


@dataclass(frozen=True, eq=False)
class SuperLayerSpec:
    number: int
    pose: Pose
    layers: list
    shape: Optional[Shape] = None
    material: Optional[str] = None


@dataclass(frozen=True, eq=False)
class AttachmentSpec:
    """A passive panel bolted to a station, e.g. the honeycomb spacer.

    Data only: a shape and a pose, no boolean solid. An exporter may turn it into
    a volume; nothing in the model does (T-032).
    """

    name: str
    pose: Pose
    shape: Shape
    material: str = "G4_Al"


@dataclass(frozen=True, eq=False)
class StationSpec:
    name: str
    pose: Pose
    super_layers: list
    shape: Optional[Shape] = None
    material: Optional[str] = "G4_AIR"
    attachments: list = field(default_factory=list)


@dataclass(frozen=True, eq=False)
class StructureSpec:
    """Detector structure outside the chambers, e.g. the yoke (T-033).

    Data only: the builder makes no node for it and no exporter sees it until a
    backend can do the boolean solids (ADR-011, ADR-017).
    """

    name: str
    pose: Pose
    shape: Optional[Shape] = None
    material: str = "G4_Fe"


@dataclass(frozen=True, eq=False)
class DetectorSpec:
    name: str
    pose: Pose
    stations: list
    shape: Optional[Shape] = None
    material: str = "G4_Galactic"
    structure: list = field(default_factory=list)


def _check_pose(pose, where):
    if not isinstance(pose, Pose):
        raise ValueError("%s: pose must be a Pose, got %r" % (where, type(pose).__name__))
    if not np.all(np.isfinite(pose.rotation)) or not np.all(np.isfinite(pose.translation)):
        raise ValueError("%s: pose has non-finite values" % where)
    deviation = np.max(np.abs(pose.rotation @ pose.rotation.T - np.eye(3)))
    if deviation > ROTATION_TOLERANCE:
        raise ValueError("%s: rotation is not orthonormal (max deviation %.3g)" % (where, deviation))
    if np.linalg.det(pose.rotation) <= 0.0:
        raise ValueError("%s: rotation is not a proper rotation (det <= 0)" % where)


def _check_shape(shape, where):
    if shape is None:
        return
    if isinstance(shape, Box):
        for name in ("dx", "dy", "dz"):
            value = getattr(shape, name)
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError("%s: box %s must be positive, got %r" % (where, name, value))
    elif isinstance(shape, Tube):
        if not np.isfinite(shape.radius) or shape.radius <= 0.0:
            raise ValueError("%s: tube radius must be positive, got %r" % (where, shape.radius))
        if not np.isfinite(shape.length) or shape.length <= 0.0:
            raise ValueError("%s: tube length must be positive, got %r" % (where, shape.length))
        if shape.inner_radius < 0.0 or shape.inner_radius >= shape.radius:
            raise ValueError(
                "%s: tube inner_radius must be in [0, radius), got %r" % (where, shape.inner_radius)
            )
        if shape.axis not in ("x", "y", "z"):
            raise ValueError("%s: tube axis must be 'x', 'y' or 'z', got %r" % (where, shape.axis))
    else:
        raise ValueError("%s: unknown shape %r" % (where, type(shape).__name__))


def _check_grid(grid, layer_shape, where):
    if not isinstance(grid, CellGrid):
        raise ValueError("%s: cells must be a CellGrid, got %r" % (where, type(grid).__name__))
    if not np.isfinite(grid.pitch) or grid.pitch <= 0.0:
        raise ValueError("%s: pitch must be positive, got %r" % (where, grid.pitch))
    if grid.count < 1:
        raise ValueError("%s: count must be >= 1, got %r" % (where, grid.count))
    if grid.first_id < 1:
        raise ValueError("%s: first_id must be >= 1, got %r" % (where, grid.first_id))
    if not np.isfinite(grid.offset):
        raise ValueError("%s: offset must be finite, got %r" % (where, grid.offset))
    _check_shape(grid.shape, where + " cell")
    if grid.material is not None and not isinstance(grid.material, str):
        raise ValueError(
            "%s: cell material must be a string, got %r" % (where, type(grid.material).__name__)
        )
    if grid.shape.aabb()[0] > grid.pitch + ROTATION_TOLERANCE:
        raise ValueError(
            "%s: cell is wider than the pitch (%.4g > %.4g)" % (where, grid.shape.aabb()[0], grid.pitch)
        )
    if isinstance(layer_shape, Box):
        used = grid.count * grid.pitch
        if used > layer_shape.dx + ROTATION_TOLERANCE:
            raise ValueError(
                "%s: cells do not fit the layer (%.4g > %.4g)" % (where, used, layer_shape.dx)
            )


def _check_number(number, where):
    """Numbers are positive ints. How many super layers and layers a station has
    is the source's concern: the CMS chambers have three and four, a custom
    station may have any count (T-030)."""
    if not isinstance(number, int) or number < 1:
        raise ValueError("%s: number must be a positive int, got %r" % (where, number))


def _validate_layer(layer, where):
    _check_number(layer.number, where)
    _check_pose(layer.pose, where)
    _check_shape(layer.shape, where)
    _check_grid(layer.cells, layer.shape, where)


def _validate_super_layer(super_layer, where):
    _check_number(super_layer.number, where)
    _check_pose(super_layer.pose, where)
    _check_shape(super_layer.shape, where)
    if not super_layer.layers:
        raise ValueError("%s: no layers" % where)
    numbers = set()
    for layer in super_layer.layers:
        if layer.number in numbers:
            raise ValueError("%s: duplicate layer number %d" % (where, layer.number))
        numbers.add(layer.number)
        _validate_layer(layer, where + " / layer %d" % layer.number)


def _validate_attachments(attachments, where):
    names = set()
    for attachment in attachments:
        if not isinstance(attachment, AttachmentSpec):
            raise ValueError(
                "%s: attachments must be AttachmentSpec, got %r"
                % (where, type(attachment).__name__)
            )
        if not isinstance(attachment.name, str) or not attachment.name:
            raise ValueError("%s: an attachment needs a non-empty name" % where)
        if attachment.name in names:
            raise ValueError("%s: duplicate attachment name %r" % (where, attachment.name))
        names.add(attachment.name)
        _check_pose(attachment.pose, where + " / " + attachment.name)
        if attachment.shape is None:
            raise ValueError("%s / %s: an attachment needs a shape" % (where, attachment.name))
        _check_shape(attachment.shape, where + " / " + attachment.name)


def _validate_station(station, where):
    if not isinstance(station.name, str) or not station.name:
        raise ValueError("%s: name must be a non-empty string" % where)
    _check_pose(station.pose, where)
    _check_shape(station.shape, where)
    if not station.super_layers and station.shape is None:
        # a station is a chamber (super layers) or a passive solid with a pose:
        # the lead wall of a prototype, a support panel (3.0.1)
        raise ValueError("%s: no super layers and no solid" % where)
    numbers = set()
    for super_layer in station.super_layers:
        if super_layer.number in numbers:
            raise ValueError("%s: duplicate super layer number %d" % (where, super_layer.number))
        numbers.add(super_layer.number)
        _validate_super_layer(super_layer, where + " / super layer %d" % super_layer.number)
    _validate_attachments(station.attachments, where)


def _validate_structure(structure, where):
    names = set()
    for part in structure:
        if not isinstance(part, StructureSpec):
            raise ValueError(
                "%s: structure must be StructureSpec, got %r" % (where, type(part).__name__)
            )
        if not isinstance(part.name, str) or not part.name:
            raise ValueError("%s: a structure entry needs a non-empty name" % where)
        if part.name in names:
            raise ValueError("%s: duplicate structure name %r" % (where, part.name))
        names.add(part.name)
        _check_pose(part.pose, where + " / " + part.name)
        _check_shape(part.shape, where + " / " + part.name)


def validate(spec):
    """Raise ValueError on the first problem found in a spec tree.

    Accepts DetectorSpec, StationSpec, SuperLayerSpec or LayerSpec.
    """
    if isinstance(spec, DetectorSpec):
        if not isinstance(spec.name, str) or not spec.name:
            raise ValueError("detector: name must be a non-empty string")
        _check_pose(spec.pose, "detector %r" % spec.name)
        _check_shape(spec.shape, "detector %r" % spec.name)
        if not spec.stations:
            raise ValueError("detector %r: no stations" % spec.name)
        names = set()
        for station in spec.stations:
            if station.name in names:
                raise ValueError("detector %r: duplicate station name %r" % (spec.name, station.name))
            names.add(station.name)
            _validate_station(station, "detector %r / station %r" % (spec.name, station.name))
        _validate_structure(spec.structure, "detector %r" % spec.name)
    elif isinstance(spec, StationSpec):
        _validate_station(spec, "station %r" % spec.name)
    elif isinstance(spec, SuperLayerSpec):
        _validate_super_layer(spec, "super layer %d" % spec.number)
    elif isinstance(spec, LayerSpec):
        _validate_layer(spec, "layer %d" % spec.number)
    else:
        raise TypeError("validate() got %r" % (type(spec).__name__,))
