"""Runtime topology (T-020).

build_station turns a StationSpec into a node tree:

    station
    └── attachment       Box panel bolted to the station (honeycomb)
    └── super layer      grouping frame, shape=None
        └── layer        grouping frame, shape=None
            └── cell     Box or Tube, from the layer CellGrid

Every node stores one pose relative to its parent (p_parent = R * p_child + t);
world_pose is composed once, top-down, and cached on the node. Nodes with
shape=None are pure grouping frames: they matter for transforms and plotting,
not for the exporter.

No I/O and no backend import: the CMS source (T-011) feeds build_station,
FrameGraph (T-021) and the exporters consume the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from mpldts.geometry.specs import Pose, Shape, validate

__all__ = ["Node", "build_station", "build_detector"]


@dataclass
class Node:
    """One element of the runtime geometry tree."""

    name: str
    kind: str  # station | superlayer | layer | cell
    pose: Pose  # parent-relative
    world_pose: Pose  # composed at build time
    frame_id: str  # unique slash path, e.g. /W0_S5_MB1/SL2/L1/C7
    shape: Optional[Shape] = None  # None = grouping frame
    material: Optional[str] = None
    parent: Optional["Node"] = None
    children: List["Node"] = field(default_factory=list)
    #: panels bolted to the node, kept apart from the geometry children
    attachments: List["Node"] = field(default_factory=list)


def _make(parent, name, kind, pose, shape, material):
    world = (parent.world_pose if parent is not None else Pose.identity()).compose(pose)
    frame_id = (parent.frame_id if parent is not None else "") + "/" + name
    return Node(name, kind, pose, world, frame_id, shape, material, parent)


def build_station(spec, parent=None):
    """Build the node tree of a StationSpec, hanging it under parent if given."""
    validate(spec)
    station = _make(parent, spec.name, "station", spec.pose, spec.shape, spec.material)
    for attachment_spec in spec.attachments:
        station.attachments.append(
            _make(
                station,
                attachment_spec.name,
                "attachment",
                attachment_spec.pose,
                attachment_spec.shape,
                attachment_spec.material,
            )
        )
    for super_layer_spec in spec.super_layers:
        super_layer = _make(
            station,
            "SL%d" % super_layer_spec.number,
            "superlayer",
            super_layer_spec.pose,
            super_layer_spec.shape,
            super_layer_spec.material,
        )
        station.children.append(super_layer)
        for layer_spec in super_layer_spec.layers:
            layer = _make(
                super_layer,
                "L%d" % layer_spec.number,
                "layer",
                layer_spec.pose,
                layer_spec.shape,
                layer_spec.material,
            )
            super_layer.children.append(layer)
            grid = layer_spec.cells
            for x, number in zip(grid.x_positions(), grid.ids()):
                layer.children.append(
                    _make(
                        layer,
                        "C%d" % number,
                        "cell",
                        Pose.translated(float(x), 0.0, 0.0),
                        grid.shape,
                        grid.material,
                    )
                )
    return station


def build_detector(spec, parent=None):
    """Build the node tree of a DetectorSpec: the detector is the root node.

    Every station of the spec hangs under it at its own pose, so one graph holds
    the whole assembly (T-030). A station is still built by build_station.
    """
    validate(spec)
    detector = _make(parent, spec.name, "detector", spec.pose, spec.shape, spec.material)
    detector.children = [build_station(station, detector) for station in spec.stations]
    return detector
