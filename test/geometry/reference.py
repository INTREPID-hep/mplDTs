"""XML reference values for the geometry oracle.

Test helper, not library code. It reads the CMS XML once and returns the
values the model must reproduce; the spec path (T-012) reuses it.

The XML Wire element is the cell entry (ADR-019): its GlobalPosition is the
cell centre in CMS coordinates.
"""

import numpy as np

from mpldts.geometry import DTGEOMETRY
from mpldts.geometry._geometry import DTGeometry

#: One chamber per wheel/station family, used by the default test run.
REPRESENTATIVE = [(-2, 1, 1), (-1, 3, 2), (0, 5, 3), (1, 3, 4), (2, 14, 4), (0, 1, 1)]

#: The super layer BUG-01 used to affect; the SL2 test still pins it.
SL2 = 2

#: Cell-centre tolerance in cm. The XML stores 3 decimals, and the model also
#: reads 3-decimal local positions, so two roundings ~5e-4 each set the floor.
#: A real pose bug is two orders of magnitude larger (SL2 is 5e-1 cm).
TOLERANCE = 2e-3


def all_chambers():
    """All (wheel, sector, station) keys in the XML, sorted."""
    return sorted(DTGEOMETRY._chamber_key_index)


def chamber_element(chamber):
    """XML element of a chamber, given its (wheel, sector, station) key."""
    return DTGEOMETRY.get(wh=chamber[0], sec=chamber[1], st=chamber[2])


def super_layer_numbers(chamber):
    """Super layer numbers present in the chamber (MB4 has only 1 and 3)."""
    return [int(sl.get("superLayerNumber")) for sl in chamber_element(chamber).iter("SuperLayer")]


def _pos(text):
    return np.asarray(DTGeometry._transform_to_pos(text), dtype=float)


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
    """Node fields of the chamber, its super layers and its layers, from the XML."""
    element = chamber_element(chamber)
    out = {
        "chamber": {"id": int(element.get("rawId")), **_node(element)},
        "super_layers": {},
        "layers": {},
    }
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
