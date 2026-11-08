"""CMS DT geometry source: XML -> StationSpec (T-011).

Reads the CMS geometry XML once, indexes chambers, super layers, layers and
cell centres at parse time, and emits the immutable specs from T-010.

The XML stores its local positions in two different frames (station frame for
super layers and layers, super-layer frame for the SL2 cells), so the poses are
derived from the *global* positions and the known super-layer orientation
instead of trusting the mixed locals. The globals stay available as the
reference for the oracle: cell_centres() returns them.

This module is the only new code allowed to import ElementTree.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from mpldts.geometry.specs import (
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
)

__all__ = ["CMSXMLSource", "DEFAULT_XML", "position"]

#: Geometry shipped with the package (cm).
DEFAULT_XML = Path(__file__).resolve().parents[1] / "DTGeometry_v3.xml"

#: CMS super-layer orientation about z, degrees. SL2 is rotated -90 degrees.
SUPER_LAYER_ROTATION_Z = {1: 0.0, 2: -90.0, 3: 0.0}

#: Wheels whose sector 0 chambers face the other way (CMS naming document).
NEGATIVE_FACE_SECTORS = (1, 4, 5, 8, 9, 12, 13)

_CHAMBER_ID = re.compile(r"Wh:(-?\d+)\s+St:(\d+)\s+Se:(\d+)")
_NUMBER = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def position(text):
    """(x, y, z) from an XML position string (the parser is the source's job)."""
    values = _NUMBER.findall(text or "")
    if len(values) < 3:
        raise ValueError("cannot read a position from %r" % (text,))
    return np.array([float(value) for value in values[:3]])


def _bounds(element):
    attrs = element.find("Bounds").attrib
    return float(attrs["width"]), float(attrs["thickness"]), float(attrs["length"])


class CMSXMLSource:
    """Geometry source for the CMS drift tube chambers."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else DEFAULT_XML
        self._chambers = {}
        self._chamber_of = {}
        self._parse()

    # -- public API --------------------------------------------------------

    def chamber_keys(self):
        """Every (wheel, sector, station) key in the file, sorted."""
        return sorted(self._chambers)

    def number_of_chambers(self):
        return len(self._chambers)

    def station(self, wheel, sector, station):
        """StationSpec for one chamber; KeyError if the chamber is absent."""
        key = (wheel, sector, station)
        return self._station_spec(key, self._record(*key))

    def record(self, wheel, sector, station):
        """Raw parse record of one chamber (read-only); KeyError if absent.

        The legacy wrappers (T-022) read the values the XML states verbatim:
        raw ids, local positions and bounds. The model reads the derived poses.
        """
        return self._record(wheel, sector, station)

    def chamber_of(self, raw_id):
        """(wheel, sector, station) of the element with this rawId."""
        try:
            return self._chamber_of[int(raw_id)]
        except (KeyError, TypeError, ValueError):
            raise KeyError("rawId %r is not in %s" % (raw_id, self.path.name)) from None

    def _record(self, wheel, sector, station):
        record = self._chambers.get((wheel, sector, station))
        if record is None:
            raise KeyError("chamber %r is not in %s" % ((wheel, sector, station), self.path.name))
        return record

    def detector(self, name="CMS", chamber_keys=None):
        """DetectorSpec with one StationSpec per chamber (all by default)."""
        keys = self.chamber_keys() if chamber_keys is None else list(chamber_keys)
        return DetectorSpec(
            name=name,
            pose=Pose.identity(),
            stations=[self.station(*key) for key in keys],
        )

    def cell_centres(self, wheel, sector, station):
        """{(sl, layer, cell): xyz} from the XML GlobalPosition (the oracle)."""
        record = self._chambers.get((wheel, sector, station))
        if record is None:
            raise KeyError("chamber %r is not in %s" % ((wheel, sector, station), self.path.name))
        centres = {}
        for super_layer in record["super_layers"]:
            for layer in super_layer["layers"]:
                for number, centre, _ in layer["cells"]:
                    centres[(super_layer["number"], layer["number"], number)] = centre
        return centres

    # -- parsing -----------------------------------------------------------

    def _parse(self):
        root = ET.parse(self.path).getroot()
        for chamber in root.iter("Chamber"):
            match = _CHAMBER_ID.search(chamber.get("Id", ""))
            if match is None:
                continue
            wheel, station, sector = (int(value) for value in match.groups())
            key = (wheel, sector, station)
            self._chambers[key] = self._read_chamber(chamber)
            for element in chamber.iter():
                raw_id = element.get("rawId")
                if raw_id is not None:
                    self._chamber_of[int(raw_id)] = key

    @staticmethod
    def _read_chamber(chamber):
        record = {
            "id": int(chamber.get("rawId")),
            "global": position(chamber.find("GlobalPosition").text),
            "local": position(chamber.find("LocalPosition").text),
            "direction": position(chamber.find("NormalVector").text),
            "bounds": _bounds(chamber),
            "super_layers": [],
        }
        for super_layer in chamber.iter("SuperLayer"):
            sl_record = {
                "raw_id": int(super_layer.get("rawId")),
                "number": int(super_layer.get("superLayerNumber")),
                "local": position(super_layer.find("LocalPosition").text),
                "global": position(super_layer.find("GlobalPosition").text),
                "bounds": _bounds(super_layer),
                "layers": [],
            }
            for layer in super_layer.iter("Layer"):
                wires = layer.find("Wires").attrib
                cells = [
                    (
                        int(wire.get("wireNumber")),
                        position(wire.get("GlobalPosition")),
                        # kept as text: only the legacy wrappers read it
                        wire.get("LocalPosition"),
                    )
                    for wire in layer.iter("Wire")
                ]
                sl_record["layers"].append(
                    {
                        "raw_id": int(layer.get("rawId")),
                        "number": int(layer.get("layerNumber")),
                        "local": position(layer.find("LocalPosition").text),
                        "global": position(layer.find("GlobalPosition").text),
                        "bounds": _bounds(layer),
                        "wires": (
                            float(wires["width"]),
                            float(wires["thickness"]),
                            float(wires["length"]),
                        ),
                        "first": int(wires["first"]),
                        "last": int(wires["last"]),
                        "cells": cells,
                    }
                )
            record["super_layers"].append(sl_record)
        return record

    # -- spec construction -------------------------------------------------

    @staticmethod
    def _station_pose(record, key):
        wheel, sector, _ = key
        direction = record["direction"]
        face = -1 if wheel < 0 else 1 if wheel > 0 else (
            -1 if sector in NEGATIVE_FACE_SECTORS else 1
        )
        ez = direction / np.linalg.norm(direction)
        ey = np.array([0.0, 0.0, 1.0]) * face
        ex = np.cross(ey, ez)
        ex = ex / np.linalg.norm(ex)
        return Pose(np.column_stack([ex, ey, ez]), record["global"])

    def _station_spec(self, key, record):
        station_pose = self._station_pose(record, key)
        rotation = station_pose.rotation
        to_station = lambda global_position: rotation.T @ (global_position - station_pose.translation)

        super_layers = []
        for sl_record in record["super_layers"]:
            number = sl_record["number"]
            sl_pose = Pose(
                Pose.rotated_z(SUPER_LAYER_ROTATION_Z.get(number, 0.0)).rotation,
                to_station(sl_record["global"]),
            )
            layer_frame = station_pose.compose(sl_pose)

            layers = []
            for layer_record in sl_record["layers"]:
                layer_pose = Pose(np.eye(3), layer_frame.inverse().apply(layer_record["global"]))
                world = layer_frame.compose(layer_pose)

                width, thickness, length = layer_record["wires"]
                count = layer_record["last"] - layer_record["first"] + 1
                first_id = layer_record["first"]
                first_centre = layer_record["cells"][0][1]
                x_first = (world.rotation.T @ (first_centre - world.translation))[0]
                offset = float(x_first + (count - 1) / 2.0 * width)

                layers.append(
                    LayerSpec(
                        number=layer_record["number"],
                        pose=layer_pose,
                        cells=CellGrid(
                            pitch=width,
                            count=count,
                            shape=Box(width, length, thickness),
                            first_id=first_id,
                            offset=offset,
                            material="GasMixture",
                        ),
                    )
                )

            super_layers.append(
                SuperLayerSpec(
                    number=number,
                    pose=sl_pose,
                    layers=layers,
                    shape=None,
                )
            )

        width, thickness, length = record["bounds"]
        return StationSpec(
            name="W%d_S%d_MB%d" % key,
            pose=station_pose,
            super_layers=super_layers,
            shape=Box(width, length, thickness),
            material="G4_AIR",
        )
