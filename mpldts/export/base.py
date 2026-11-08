"""Backend seam for the exporters (T-052).

The model is backend neutral; an exporter only walks placed solids. A sink gets
every solid node with its mother and the pose already folded down to it:

    station           -> :VOLU placed in the world
      super layer     -> grouping frame, folded into the cells
        layer         -> grouping frame, folded into the cells
          cell        -> :VOLU placed in the station
      honeycomb       -> :VOLU placed in the station

Grouping nodes (shape=None) never become volumes; they only contribute a pose.
The walk is the same for every backend (a .tg writer, GDML, pyg4ometry), so the
sink is the only thing a new backend has to implement. Nothing here imports a
backend, and nothing in the core imports this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Protocol

from mpldts.geometry.model import Node
from mpldts.geometry.specs import Pose

__all__ = [
    "VolumePlacement",
    "VolumeSink",
    "RecordingSink",
    "iter_volume_placements",
    "export_volumes",
]


@dataclass
class VolumePlacement:
    """One solid to place: its node, its mother (None = the world) and the pose."""

    node: Node
    mother: Optional[Node]
    pose_in_mother: Pose  # grouping nodes folded in


class VolumeSink(Protocol):
    """Minimal contract every exporter backend implements."""

    def begin(self, root: Node) -> None: ...

    def place(self, node: Node, mother: Optional[Node], pose_in_mother: Pose) -> None: ...

    def end(self) -> None: ...


@dataclass
class RecordingSink:
    """Sink that only records the placements; the test double for any backend."""

    placements: List[VolumePlacement] = field(default_factory=list)
    root: Optional[Node] = None

    def begin(self, root: Node) -> None:
        self.root = root

    def place(self, node: Node, mother: Optional[Node], pose_in_mother: Pose) -> None:
        self.placements.append(VolumePlacement(node, mother, pose_in_mother))

    def end(self) -> None:
        pass


def iter_volume_placements(root: Node) -> Iterable[VolumePlacement]:
    """Pre-order walk that folds nodes without a solid into the next placement.

    A node with a shape becomes a volume of its mother; a grouping node only
    contributes its pose, so its children hang off the same mother. Attachments
    come after the regular children, so the honeycomb is placed after the cells.
    """

    def walk(node, mother, pose_in_mother):
        if node.shape is not None:
            yield VolumePlacement(node, mother, pose_in_mother)
            mother = node
            pose_in_mother = Pose.identity()
        for child in node.children:
            yield from walk(child, mother, pose_in_mother.compose(child.pose))
        for attachment in node.attachments:
            yield from walk(attachment, mother, pose_in_mother.compose(attachment.pose))

    yield from walk(root, None, root.pose)


def export_volumes(root: Node, sink: VolumeSink) -> None:
    """Drive any backend from the placement walk."""
    sink.begin(root)
    for placement in iter_volume_placements(root):
        sink.place(placement.node, placement.mother, placement.pose_in_mother)
    sink.end()
