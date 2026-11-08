"""Station view: what the plotting patches draw (T-022, T-030).

A Station is a view over two things:

    build_station(spec)     node tree, with parent-relative poses
    FrameGraph / FrameView  every frame, including the plotting ones

It holds no per-event data. The values a patch colours are the `(sl, l, w)`
table the patch is given (ADR-024), so one station can draw an event without
being copied and without any cell carrying a mutable attribute.

Any `StationSpec` builds a station (T-030). A CMS chamber reaches this class
through `CMSXMLSource().station(wheel, sector, station)`.
"""

import numpy as np

from mpldts.geometry.dt_frame import DTFrame
from mpldts.geometry.frames import FrameGraph, FrameView
from mpldts.geometry.model import build_station
from mpldts.geometry.specs import Pose
from mpldts.geometry.super_layer import SuperLayer


def _unit(vector):
    return vector / np.linalg.norm(vector)


def _face_from_pose(node):
    """1 when the station length axis points up the detector z axis, else -1.

    The legacy face factor of a CMS chamber is stated by its wheel and sector;
    for any other station the pose is the only statement (T-031).
    """
    return 1.0 if node.world_pose.rotation[2, 1] >= 0.0 else -1.0


def _add_natural_views(graph, node, face):
    """Register StationNvPhi, StationNvEta and SL13Center.

    The two views are the ones the plotting patches invert through; the face
    orientation factor is the value stated by the pose. SL13Center is the
    geometrical centre of the outermost super layers, which the AM trigger
    primitives are measured from (AMDTSegments' reference frame).
    """
    station_frame = node.frame_id

    # phi view: a rotation, the station frame to the view frame
    ez = np.array([0.0, 0.0, -1.0])
    ey = np.array([0.0, -1.0, 0.0]) * face
    ex = _unit(np.cross(ey, ez))
    graph.add_virtual(
        station_frame + "/StationNvPhi", station_frame, Pose(np.column_stack([ex, ey, ez]).T)
    )

    # eta view
    ex = np.array([-1.0, 0.0, 0.0]) * face
    ey = _unit(np.cross(ez, ex))
    graph.add_virtual(
        station_frame + "/StationNvEta", station_frame, Pose(np.column_stack([ex, ey, ez]).T)
    )

    # centre of the outermost super layers
    if node.children:
        first = node.children[0].pose.translation
        last = node.children[-1].pose.translation
        graph.add_virtual(
            station_frame + "/SL13Center", station_frame, Pose.translated(*((first + last) / 2.0))
        )


def _extent(node):
    """The eight corners of a node box, in the node frame.

    A primitive states its box; a grouping frame (the CMS super layers and
    layers carry no solid of their own) takes the box that contains its
    children, so the plotting patches still draw its outline.
    """
    if node.shape is not None:
        width, length, thickness = node.shape.aabb()
        half = np.array([width, length, thickness]) / 2.0
        return np.array(
            [
                [sx * half[0], sy * half[1], sz * half[2]]
                for sx in (-1.0, 1.0)
                for sy in (-1.0, 1.0)
                for sz in (-1.0, 1.0)
            ]
        )
    if not node.children:
        return np.zeros((1, 3))
    to_node = node.world_pose.inverse()
    return np.vstack([to_node.apply(node.world_pose.apply(_extent(child))) for child in node.children])


def _bounds(node):
    """(width, thickness, length) of a node, in the node frame."""
    corners = _extent(node)
    width, length, thickness = corners.max(axis=0) - corners.min(axis=0)
    return (float(width), float(thickness), float(length))


def _plane_local(position, axis, across):
    """The cell convention of the XML: super layer plane coordinates and the
    station z.

    The CMS source states the SL2 cells in the plane of their own super layer and
    the plotting patches draw cells unrotated in both views, so a station built
    from a spec derives them the same way.
    """
    return np.array([float(position @ axis), float(position @ across), float(position[2])])


def _record_for(node):
    """The record shape the view classes read, derived from a node tree.

    The local positions are taken in the station frame and the globals from the
    composed world pose; the raw ids only have to be unique, they look the
    children up.
    """
    station = node.world_pose
    to_station = station.inverse()
    ids = iter(range(1, 10 ** 7))

    def local(part):
        return to_station.apply(part.world_pose.translation)

    record = {
        "id": node.name,
        "local": local(node),
        "global": station.translation,
        "direction": station.rotation[:, 2],
        "bounds": _bounds(node),
        "super_layers": [],
    }
    for super_layer in node.children:
        axis = super_layer.pose.rotation[:, 0]
        across = super_layer.pose.rotation[:, 1]
        sl_record = {
            "raw_id": next(ids),
            "number": int(super_layer.name[2:]),
            "local": local(super_layer),
            "global": super_layer.world_pose.translation,
            "bounds": _bounds(super_layer),
            "layers": [],
        }
        for layer in super_layer.children:
            sl_record["layers"].append(
                {
                    "raw_id": next(ids),
                    "number": int(layer.name[1:]),
                    "local": local(layer),
                    "global": layer.world_pose.translation,
                    "bounds": _bounds(layer),
                    "cells": [],
                    "cell_locals": {
                        int(cell.name[1:]): _plane_local(local(cell), axis, across)
                        for cell in layer.children
                    },
                }
            )
        record["super_layers"].append(sl_record)
    return record


class Station(DTFrame):
    """
    A CMS Drift Tube chamber, or any other station, as a drawing view.

    Attributes
    ----------
        super_layers : list
            List of super layers in the station.

        Others inherit from ``mpldts.geometry.DTFrame``... (e.g. id, local_center, global_center, direction, etc.)
    """

    @classmethod
    def from_spec(cls, spec, wheel=None, sector=None, number=None):
        """A Station view over any StationSpec: the one way to build a station.

        The node tree and the frame graph are built here, and the values the
        view classes read (local centres, bounds, direction) are derived from
        the node tree.

        :param spec: The station to build.
        :type spec: StationSpec
        :param wheel: Wheel of the CMS chamber this station is, for the callers
            that label a plot with it (default None: not a CMS chamber).
        :type wheel: int, optional
        :param sector: Sector of the CMS chamber, as for wheel.
        :type sector: int, optional
        :param number: Station type of the CMS chamber, as for wheel.
        :type number: int, optional
        :return: The station.
        :rtype: Station
        """
        node = build_station(spec)
        graph = FrameGraph()
        graph.add_nodes(node)
        _add_natural_views(graph, node, _face_from_pose(node))

        station = object.__new__(cls)
        station._wheel, station._sector, station._number = wheel, sector, number
        station._name = spec.name
        station._bind(_record_for(node), node, graph)
        return station

    def _bind(self, record, node, graph):
        """Attach this view to a record, its node tree and their frame graph."""
        self.id = record["id"]
        self.local_center = record["local"]
        self.global_center = record["global"]
        self.direction = record["direction"]
        self.bounds = record["bounds"]

        # == The station is a view over the shared tree and graph
        self._node = node
        self._graph = graph
        self.transformer = FrameView(graph, node)

        # rawId -> (node, record), for the child views
        self._parts = {}
        for sl_record, sl_node in zip(record["super_layers"], node.children):
            self._parts[sl_record["raw_id"]] = (sl_node, sl_record)
            for layer_record, layer_node in zip(sl_record["layers"], sl_node.children):
                self._parts[layer_record["raw_id"]] = (layer_node, layer_record)

        self._super_layers = [
            SuperLayer(rawId=sl_record["raw_id"], parent=self)
            for sl_record in record["super_layers"]
        ]

    # == Getters

    @property
    def wheel(self):
        """
        Wheel position within CMS, or None for a station that is not a CMS chamber.

        :rtype: int
        """
        return self._wheel

    @property
    def sector(self):
        """
        Sector position within CMS, or None for a station that is not a CMS chamber.

        :rtype: int
        """
        return self._sector

    @property
    def name(self):
        """
        Name of the station: the name of its spec.

        :rtype: str
        """
        return self._name

    @property
    def super_layers(self):
        """
        Get all the super layers in the station.

        :return: List of super layers in the station.
        :rtype: list
        """
        return self._super_layers

    def super_layer(self, super_layer_number):
        """
        Get a super layer by its number. if the super layer does not exist, it returns None.

        :param super_layer_number: Number of the super layer.
        :type super_layer_number: int
        :return: Super layer with the specified number.
        :rtype: SuperLayer
        """
        return next((sl for sl in self._super_layers if sl.number == super_layer_number), None)

    def _legacy_part(self, raw_id):
        """(node, record) of a super layer or layer of this station, by rawId."""
        try:
            return self._parts[int(raw_id)]
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                "rawId %r is not a super layer or layer of station %s" % (raw_id, self.name)
            ) from None
