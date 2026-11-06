"""T-024: lazy XML shim, explicit attribute names, one build per chamber."""

import subprocess
import sys

from mpldts.geometry import DTGeometry, Station


def test_import_does_not_parse_the_geometry_xml():
    code = (
        "import mpldts.geometry as g; "
        "assert g._geometry.DTGEOMETRY._geometry is None, 'parsed at import'; "
        "print('lazy')"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "lazy"


def test_bounds_and_wires_do_not_depend_on_attribute_order(tmp_path):
    path = tmp_path / "geometry.xml"
    path.write_text(
        '<DTGeometry><Chamber Id=" Wh:0 St:1 Se:1 " rawId="1">'
        '<Bounds length="251.1" width="218" thickness="36.2"/>'
        '<Wires last="49" first="1" length="234.8" width="4.2" thickness="1.3"/>'
        "</Chamber></DTGeometry>"
    )
    geometry = DTGeometry(path)

    assert geometry.get("Bounds", wh=0, sec=1, st=1) == (218.0, 36.2, 251.1)
    assert geometry.get("WiresSize", wh=0, sec=1, st=1) == (4.2, 1.3, 234.8)
    assert geometry.get("WiresRange", wh=0, sec=1, st=1) == (1, 49)


def test_one_chamber_is_built_once():
    first = Station(-2, 1, 2)
    second = Station(-2, 1, 2)
    other = Station(0, 5, 3)

    assert first is not second
    assert first.local_center == second.local_center
    assert first._node is second._node
    assert first._graph is second._graph
    assert other._node is not first._node
