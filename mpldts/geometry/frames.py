"""Frame graph and scoped frame views (T-021).

One graph holds one edge per parent/child pose; a FrameView is bound to a
node and resolves the legacy names in that node's scope (Station, SuperLayer,
SL{n}, Layer, Cell, CMS/World). The legacy TransformManager contract is kept:

- graph.matrix(from, to) is a Pose with p_to = M.apply(p_from), the same
  convention as TransformManager.get_transformation(from, to);
- get_transformation warns and returns None when there is no path, while
  transform raises ValueError;
- type="point" gets the translation, type="vector" only the rotation.

No pytransform3d, XML or backend import: the graph is the single source of
truth for frames and the node tree (T-020) fills it.
"""

from __future__ import annotations

import warnings
from collections import deque

import numpy as np

from mpldts.geometry.specs import ROTATION_TOLERANCE, Pose

__all__ = ["FrameGraph", "FrameView", "WORLD"]

#: Name of the graph root frame (the CMS frame for CMS geometries).
WORLD = "World"

#: Alias -> node kind, for the names resolved in scope.
ALIASES = {
    "Station": "station",
    "Layer": "layer",
    "Cell": "cell",
}


class FrameGraph:
    """Poses between named frames, with a cache per (from, to) pair."""

    def __init__(self, root=WORLD):
        self.root = root
        self._edges = {root: {}}
        self._cache = {}

    # -- structure ------------------------------------------------------

    def add_edge(self, child, parent, pose):
        """Register the pose of child in parent (p_parent = pose * p_child)."""
        if not isinstance(pose, Pose):
            raise TypeError("pose must be a Pose, got %r" % (type(pose).__name__,))
        deviation = float(np.max(np.abs(pose.rotation @ pose.rotation.T - np.eye(3))))
        if deviation > ROTATION_TOLERANCE:
            raise ValueError("edge %s -> %s: rotation is not orthonormal" % (child, parent))
        self._edges.setdefault(child, {})[parent] = pose
        self._edges.setdefault(parent, {})[child] = pose.inverse()
        self._cache.clear()

    def remove_edge(self, child, parent):
        self._edges.get(child, {}).pop(parent, None)
        self._edges.get(parent, {}).pop(child, None)
        for frame in (child, parent):
            if frame != self.root and not self._edges.get(frame):
                self._edges.pop(frame, None)
        self._cache.clear()

    def add_virtual(self, name, relative_to, pose):
        """A frame that is not a geometry node (StationNvPhi, SL13Center, ...)."""
        self.add_edge(name, relative_to, pose)

    def add_nodes(self, root, parent_frame=None):
        """Register a node tree built by build_station (T-020)."""
        if parent_frame is None:
            parent_frame = root.parent.frame_id if root.parent is not None else self.root
        self.add_edge(root.frame_id, parent_frame, root.pose)
        for child in root.children:
            self.add_nodes(child, root.frame_id)
        for attachment in root.attachments:
            self.add_nodes(attachment, root.frame_id)

    def frames(self):
        """Every frame name in the graph."""
        return set(self._edges)

    def has(self, frame):
        return frame in self._edges

    # -- queries --------------------------------------------------------

    def matrix(self, from_frame, to_frame):
        """Pose mapping from_frame coordinates to to_frame, or None if no path."""
        if from_frame == to_frame:
            return Pose.identity()
        key = (from_frame, to_frame)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        if from_frame not in self._edges or to_frame not in self._edges:
            return None
        queue = deque([(from_frame, Pose.identity())])
        seen = {from_frame}
        while queue:
            current, accumulated = queue.popleft()
            for neighbour, edge in self._edges[current].items():
                if neighbour in seen:
                    continue
                step = edge.compose(accumulated)
                if neighbour == to_frame:
                    self._cache[key] = step
                    return step
                seen.add(neighbour)
                queue.append((neighbour, step))
        return None

    def get_transformation(self, from_frame, to_frame):
        """4x4 matrix for from -> to; warns and returns None when there is no path."""
        pose = self.matrix(from_frame, to_frame)
        if pose is None:
            warnings.warn(
                "No transformation path found from %s to %s." % (from_frame, to_frame)
            )
            return None
        return pose.matrix()

    def transform(self, points, from_frame, to_frame, kind="point"):
        """Transform points (kind="point") or directions (kind="vector")."""
        pose = self.matrix(from_frame, to_frame)
        if pose is None:
            raise ValueError(
                "No transformation path found from %s to %s." % (from_frame, to_frame)
            )
        return pose.apply(points, kind)


class FrameView:
    """The graph seen from one node: legacy names resolve inside its scope."""

    def __init__(self, graph, node):
        self.graph = graph
        self.node = node

    # -- name resolution ------------------------------------------------

    def _scopes(self):
        node = self.node
        while node is not None:
            yield node
            node = node.parent

    def _scoped_name(self, name):
        """A frame registered under an ancestor scope, e.g. StationNvPhi."""
        for scope in self._scopes():
            candidate = scope.frame_id + "/" + name
            if self.graph.has(candidate):
                return candidate
        return None

    def _alias(self, name):
        """Resolve a legacy name in scope; None when it is not in scope."""
        if name in ("CMS", WORLD):
            return self.graph.root
        kind = ALIASES.get(name)
        if kind is not None:
            for scope in self._scopes():
                if scope.kind == kind:
                    return scope.frame_id
            return None
        if name.startswith("SL") and name[2:].isdigit():
            for scope in self._scopes():
                if scope.name == name:
                    return scope.frame_id
                if scope.kind == "station":
                    for child in scope.children:
                        if child.name == name:
                            return child.frame_id
            return None
        return self._scoped_name(name)

    def _resolve(self, name):
        if self.graph.has(name):
            return name
        alias = self._alias(name)
        if alias is not None:
            return alias
        raise KeyError(self._unknown(name))

    def _unknown(self, name):
        return "%r is not a frame in the scope of %s; available: %s" % (
            name,
            self.node.frame_id,
            ", ".join(sorted(self.available_frames)),
        )

    def _resolve_for_add(self, from_name, to_name):
        try:
            to_frame = self._resolve(to_name)
        except KeyError:
            to_frame = None
        try:
            from_frame = self._resolve(from_name)
        except KeyError:
            from_frame = None
        if from_frame is None and to_frame is None:
            raise KeyError(self._unknown(from_name))
        if from_frame is None:
            from_frame = to_frame + "/" + from_name
        if to_frame is None:
            to_frame = from_frame + "/" + to_name
        return from_frame, to_frame

    # -- legacy TransformManager API ------------------------------------

    @property
    def available_frames(self):
        """Frame ids plus the legacy names that resolve in scope (T-056).

        The ids alone are not enough: the legacy TransformManager API (and
        `AMDTSegment`'s reference-frame check) looks a frame up here before
        asking for a transformation, so every name `_alias` accepts has to be a
        member. One pass over the frame basenames; 0.13 ms on a CMS chamber.
        """
        frames = set(self.graph.frames())
        names = set(ALIASES) | {WORLD, "CMS"}
        names.update(frame.rsplit("/", 1)[-1] for frame in frames)
        frames.update(name for name in names if self._alias(name) is not None)
        return frames

    def get_transformation(self, from_frame, to_frame):
        try:
            child = self._resolve(from_frame)
            parent = self._resolve(to_frame)
        except KeyError:
            warnings.warn(
                "No transformation path found from %s to %s." % (from_frame, to_frame)
            )
            return None
        return self.graph.get_transformation(child, parent)

    def transform(self, points, from_frame, to_frame, type="point"):
        try:
            child = self._resolve(from_frame)
            parent = self._resolve(to_frame)
        except KeyError as error:
            raise ValueError(str(error))
        return self.graph.transform(points, child, parent, kind=type)

    def add(
        self,
        from_frame,
        to_frame,
        transformation_matrix=None,
        rotation_matrix=None,
        translation_vector=None,
    ):
        """Legacy TransformManager.add: the matrix maps from_frame to to_frame."""
        if transformation_matrix is not None:
            pose = Pose.from_matrix(transformation_matrix)
        else:
            rotation = (
                np.eye(3) if rotation_matrix is None else np.asarray(rotation_matrix, dtype=float)
            )
            translation = (
                np.zeros(3)
                if translation_vector is None
                else np.asarray(translation_vector, dtype=float)
            )
            pose = Pose(rotation, translation)
        child, parent = self._resolve_for_add(from_frame, to_frame)
        self.graph.add_edge(child, parent, pose)

    def remove(self, from_frame, to_frame):
        self.graph.remove_edge(self._resolve(from_frame), self._resolve(to_frame))

    def __str__(self):
        aliases = [
            name
            for name in list(ALIASES) + ["CMS", WORLD, "SL1", "SL2", "SL3"]
            if self._alias(name) is not None
        ]
        return "FrameView: %s (%d frames)" % (" <-> ".join(aliases), len(self.available_frames))
