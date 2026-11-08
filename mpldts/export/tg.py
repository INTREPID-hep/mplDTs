"""Geant4 ASCII (.tg) writer (T-052).

Implements :class:`mpldts.export.base.VolumeSink` and writes the format that
`G4tgbVolumeMgr` reads:

    :SOLID Solid_X BOX hx hy hz
    :VOLU  X Solid_X G4_AIR
    :ROTM  RM_1 1. 0. 0. 0. 1. 0. 0. 0. 1.
    :PLACE X 1 world R0 0.*cm 0.*cm 0.*cm

One file is one or more stations; the world volume is not written, it belongs to
the document that includes the file (`geometry_concentrator.tg` in
DTG4Simulator defines `world` and `R0`).

Names come from the node tree: a station keeps its node name, cells become
`DriftCell_<station>_<SL>` and attachments `<name>_<station>`. Because the
simulator includes every station file in one document, names and rotation
matrices are qualified by the exported root name, so two files never collide.

A consumer whose Geant4 code parses those names passes `name_of`: a callable
`node -> str or None` overriding the base name of a node (None keeps the
default). DTG4Simulator decodes `DriftCell_<w>_Sec<s>_St<n>_SL<n>_<encoding>`
from the volume name, and the layer and wire from the copy number, so it supplies
both sides of that contract with the hook (T-057).

Copy numbers restart for every volume placed in a mother, so a cell volume
numbers its copies 1..n exactly as the reference CMS generator does; the
downstream sensitive detectors decode the cell from that copy number.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import numpy as np

from mpldts._deprecation import deprecated
from mpldts.geometry.model import Node
from mpldts.geometry.specs import Box, Shape, Tube

__all__ = ["TgSink", "TgFormatError"]

#: Rotation that takes the Geant4 solid axis (+z) onto the shape axis.
_AXIS_ALIGNMENT = {
    "x": np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]]),
    "y": np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]]),
    "z": np.eye(3),
}


class TgFormatError(ValueError):
    """The tree cannot be written as a .tg file."""


def _clean(name: str) -> str:
    """A Geant4 name: letters, digits, dash and underscore, never starting with a digit.

    The dash is part of the CMS naming contract: the simulator's decoders read
    the wheel as "_W-1" (DTSimUtils.hh), so a negative wheel must keep its sign.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", str(name))
    return "_" + cleaned if cleaned[:1].isdigit() else cleaned


def _ancestor(node: Optional[Node], kind: str) -> Optional[Node]:
    while node is not None and node.kind != kind:
        node = node.parent
    return node


def _shape_key(shape: Shape):
    if isinstance(shape, Box):
        return ("box", round(shape.dx, 9), round(shape.dy, 9), round(shape.dz, 9))
    if isinstance(shape, Tube):
        return (
            "tube",
            round(shape.radius, 9),
            round(shape.length, 9),
            round(shape.inner_radius, 9),
            shape.symmetry_axis(),
        )
    raise TgFormatError("no .tg solid for shape %r" % (type(shape).__name__,))


def _solid_line(name: str, shape: Shape) -> str:
    if isinstance(shape, Box):
        return ":SOLID %s BOX %.6f*cm %.6f*cm %.6f*cm" % (
            name,
            shape.dx / 2,
            shape.dy / 2,
            shape.dz / 2,
        )
    if isinstance(shape, Tube):
        return ":SOLID %s TUBE %.6f*cm %.6f*cm %.6f*cm" % (
            name,
            shape.inner_radius,
            shape.radius,
            shape.length / 2,
        )
    raise TgFormatError("no .tg solid for shape %r" % (type(shape).__name__,))


def _solid_axis(shape: Shape) -> str:
    axis = shape.symmetry_axis()
    if axis is None:
        return "z"
    if axis not in _AXIS_ALIGNMENT:
        raise TgFormatError("unsupported tube axis %r" % (axis,))
    return axis


class TgSink:
    """Write the placements of one tree as a Geant4 ASCII geometry file."""

    def __init__(self, target, world: str = "world", name_of=None):
        #: a path or any object with `write` (a StringIO in tests)
        self._target = target
        self._world = _clean(world)
        #: optional `node -> str or None` override of the volume base name
        if name_of is not None:
            deprecated(
                "TgSink(name_of=...)",
                "the node names (3.0 emits DriftCell_<station>_<SL>, T-072)",
            )
        self._name_of = name_of
        self._lines: List[str] = []
        self._root: Optional[Node] = None
        self._rotations: Dict[tuple, str] = {}
        self._volumes: Dict[tuple, str] = {}
        self._solids: Dict[tuple, str] = {}
        self._copies: Dict[str, int] = {}

    # -- VolumeSink --------------------------------------------------------

    def begin(self, root: Node) -> None:
        self._root = root
        self._lines = []
        self._rotations = {}
        self._volumes = {}
        self._solids = {}
        self._copies = {}
        self._lines.append("// mplDTs .tg export: %s" % _clean(root.name))
        self._lines.append("")

    def place(self, node: Node, mother: Optional[Node], pose_in_mother) -> None:
        if node.material is None:
            raise TgFormatError("%s %r has no material" % (node.kind, node.name))
        volume = self._volume_name(node)
        self._emit_volume(volume, node)
        rotation = pose_in_mother.rotation @ _AXIS_ALIGNMENT[_solid_axis(node.shape)]
        mother_name = self._mother_name(mother)
        copy = self._copies.get((mother_name, volume), 0) + 1
        self._copies[(mother_name, volume)] = copy
        self._lines.append(
            ":PLACE %s %d %s %s %.6f*cm %.6f*cm %.6f*cm"
            % (
                volume,
                copy,
                mother_name,
                self._rotation_name(rotation),
                pose_in_mother.translation[0],
                pose_in_mother.translation[1],
                pose_in_mother.translation[2],
            )
        )

    def end(self) -> None:
        text = "\n".join(self._lines) + "\n"
        if hasattr(self._target, "write"):
            self._target.write(text)
        else:
            with open(self._target, "w") as handle:
                handle.write(text)

    # -- naming ------------------------------------------------------------

    def _mother_name(self, mother: Optional[Node]) -> str:
        return self._world if mother is None else self._volume_name(mother)

    def _volume_name(self, node: Node) -> str:
        """Volume name of a node, cached by (name, shape) so a solid is defined once."""
        base = self._base_name(node)
        key = (base, _shape_key(node.shape))
        name = self._volumes.get(key)
        if name is not None:
            return name
        taken = set(self._volumes.values())
        name = base
        index = 2
        while name in taken:
            name = "%s_%d" % (base, index)
            index += 1
        self._volumes[key] = name
        return name

    def _base_name(self, node: Node) -> str:
        if self._name_of is not None:
            custom = self._name_of(node)
            if custom is not None:
                return _clean(custom)
        if node is self._root or node.kind in ("detector", "station"):
            return _clean(node.name)
        station = _ancestor(node, "station")
        if node.kind == "cell":
            super_layer = _ancestor(node, "superlayer")
            sl = "" if super_layer is None else "_" + _clean(super_layer.name)
            if station is None:
                return _clean("DriftCell") + sl
            return _clean("DriftCell") + "_" + _clean(station.name) + sl
        suffix = "" if station is None else "_" + _clean(station.name)
        return _clean(node.name) + suffix

    def _emit_volume(self, volume: str, node: Node) -> None:
        key = (volume, _shape_key(node.shape))
        if key in self._solids:
            return
        solid = "Solid_" + volume
        self._solids[key] = solid
        self._lines.append(_solid_line(solid, node.shape))
        self._lines.append(":VOLU %s %s %s" % (volume, solid, node.material))
        self._lines.append("")

    def _rotation_name(self, rotation) -> str:
        if np.allclose(rotation, np.eye(3), atol=1e-9):
            return "R0"
        key = tuple(np.round(np.asarray(rotation, dtype=float), 9).flatten())
        name = self._rotations.get(key)
        if name is None:
            root = "" if self._root is None else _clean(self._root.name)
            name = "RM_%s_%d" % (root, len(self._rotations) + 1)
            self._rotations[key] = name
            values = " ".join("%.6f" % value for value in key)
            self._lines.append(":ROTM %s %s" % (name, values))
        return name
