"""Shared XML reference readers, spec helpers and fixtures for the test suite.

The helpers below are test helpers, not library code: they read the CMS XML
once and return the values the model must reproduce. The spec path reuses
them.

The XML Wire element is the cell entry (ADR-019): its GlobalPosition is the
cell centre in CMS coordinates.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

from mpldts.geometry import Station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import Pose

#: The source of truth: the CMS geometry the model is checked against. The
#: library no longer wraps it, so the oracle reads the file directly.
XML = Path(__file__).resolve().parents[1] / "mpldts" / "geometry" / "DTGeometry_v3.xml"

#: One chamber per wheel/station family, used by the default test run.
REPRESENTATIVE = [(-2, 1, 1), (-1, 3, 2), (0, 5, 3), (1, 3, 4), (2, 14, 4), (0, 1, 1)]

#: The super layer BUG-01 used to affect; the SL2 test still pins it.
SL2 = 2

#: Cell-centre tolerance in cm. The XML stores 3 decimals, and the model also
#: reads 3-decimal local positions, so two roundings ~5e-4 each set the floor.
#: A real pose bug is two orders of magnitude larger (SL2 is 5e-1 cm).
TOLERANCE = 2e-3

_CHAMBERS = None


def _chambers():
    """{(wheel, sector, station): Chamber element}, parsed once."""
    global _CHAMBERS
    if _CHAMBERS is None:
        index = {}
        for chamber in ET.parse(XML).getroot().iter("Chamber"):
            fields = dict(part.split(":") for part in chamber.get("Id").split())
            index[(int(fields["Wh"]), int(fields["Se"]), int(fields["St"]))] = chamber
        _CHAMBERS = index
    return _CHAMBERS


def all_chambers():
    """All (wheel, sector, station) keys in the XML, sorted."""
    return sorted(_chambers())


def chamber_element(chamber):
    """XML element of a chamber, given its (wheel, sector, station) key."""
    return _chambers()[tuple(chamber)]


def super_layer_numbers(chamber):
    """Super layer numbers present in the chamber (MB4 has only 1 and 3)."""
    return [int(sl.get("superLayerNumber")) for sl in chamber_element(chamber).iter("SuperLayer")]


def _pos(text):
    return np.asarray([float(value) for value in text.strip().strip("()").split(",")], dtype=float)


def _bounds(element):
    attrs = element.find("Bounds").attrib
    return (float(attrs["width"]), float(attrs["thickness"]), float(attrs["length"]))


def _node(element):
    return {
        "local": _pos(element.find("LocalPosition").text),
        "global": _pos(element.find("GlobalPosition").text),
        "direction": _pos(element.find("NormalVector").text),
        "bounds": _bounds(element),
    }


def cell_centres(chamber):
    """{(sl, layer, cell): (x, y, z)} from the XML GlobalPosition."""
    out = {}
    for sl in chamber_element(chamber).iter("SuperLayer"):
        slno = int(sl.get("superLayerNumber"))
        for layer in sl.iter("Layer"):
            lno = int(layer.get("layerNumber"))
            for wire in layer.iter("Wire"):
                out[(slno, lno, int(wire.get("wireNumber")))] = _pos(wire.get("GlobalPosition"))
    return out


def node_fields(chamber):
    """Node fields of the chamber, its super layers and its layers, from the XML.

    The rawId is not among them: it belonged to the XML-backed wrapper 3.0
    deletes, and nothing in the model reads it.
    """
    element = chamber_element(chamber)
    out = {"chamber": _node(element), "super_layers": {}, "layers": {}}
    for sl in element.iter("SuperLayer"):
        slno = int(sl.get("superLayerNumber"))
        out["super_layers"][slno] = _node(sl)
        for layer in sl.iter("Layer"):
            out["layers"][(slno, int(layer.get("layerNumber")))] = _node(layer)
    return out


def compare_cell_centres(computed, expected, tolerance=TOLERANCE):
    """Diff computed cell centres against the reference.

    :param computed: {(sl, layer, cell): xyz} from the model.
    :param expected: {(sl, layer, cell): xyz} from the XML.
    :param tolerance: max per-axis deviation in cm.
    :return: list of failure strings; empty means they agree.
    """
    failures = []
    for key in sorted(set(expected) - set(computed)):
        failures.append("missing cell sl=%d layer=%d cell=%d" % key)
    for key in sorted(set(computed) - set(expected)):
        failures.append("unexpected cell sl=%d layer=%d cell=%d" % key)
    for key in sorted(set(computed) & set(expected)):
        got = np.asarray(computed[key], dtype=float)
        ref = np.asarray(expected[key], dtype=float)
        error = float(np.max(np.abs(got - ref)))
        if error > tolerance:
            failures.append(
                "cell sl=%d layer=%d cell=%d: expected %s got %s (|d|max=%.4g cm)"
                % (key + (tuple(np.round(ref, 4)), tuple(np.round(got, 4)), error))
            )
    return failures


# -- the spec path ---------------------------------------------------------


def spec_cell_centres(station_spec):
    """{(sl, layer, cell): xyz} in the parent frame of the station.

    Composes station -> super layer -> layer -> cell poses.
    """
    centres = {}
    for super_layer in station_spec.super_layers:
        super_layer_frame = station_spec.pose.compose(super_layer.pose)
        for layer in super_layer.layers:
            layer_frame = super_layer_frame.compose(layer.pose)
            grid = layer.cells
            for x, number in zip(grid.x_positions(), grid.ids()):
                centre = layer_frame.compose(Pose.translated(x, 0.0, 0.0)).apply((0.0, 0.0, 0.0))
                centres[(super_layer.number, layer.number, number)] = centre
    return centres


def station_cell_centres(station):
    """{(sl, layer, cell): xyz} from the Cell -> CMS transform of a station view."""
    out = {}
    for sl in station.super_layers:
        for layer in sl.layers:
            for cell in layer.cells:
                out[(sl.number, layer.number, cell.number)] = cell.transformer.transform(
                    (0, 0, 0), "Cell", "CMS"
                )
    return out


# -- fixtures --------------------------------------------------------------


@pytest.fixture(scope="session")
def source():
    """One CMSXMLSource for the whole run: the XML is parsed once."""
    return CMSXMLSource()


@pytest.fixture(scope="session")
def built_station(source):
    """A session cache of Station views, exposed as station_of(chamber).

    A station build is expensive enough that every test needing the same
    chamber should share the one already built.
    """
    cache = {}

    def station_of(chamber):
        if chamber not in cache:
            cache[chamber] = Station.from_spec(source.station(*chamber), *chamber)
        return cache[chamber]

    return station_of
