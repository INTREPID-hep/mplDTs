"""T-011: the CMS XML source emits specs that match the XML."""

from pathlib import Path

import numpy as np
import pytest

from mpldts.geometry import specs
from mpldts.geometry.sources import CMSXMLSource

from .spec_centres import cell_centres

SOURCE = CMSXMLSource()

CHAMBERS = [(-2, 1, 1), (0, 1, 1), (2, 14, 4)]


def test_chamber_index_covers_the_file():
    keys = SOURCE.chamber_keys()

    assert len(keys) == 250
    assert keys == sorted(keys)
    assert keys[0][0] == -2 and keys[-1][0] == 2


@pytest.mark.parametrize("chamber", CHAMBERS)
def test_station_spec_validates(chamber):
    station = SOURCE.station(*chamber)

    specs.validate(station)
    assert station.material == "G4_AIR"
    assert [sl.number for sl in station.super_layers] == [1, 3, 2] or len(station.super_layers) == 2


def test_grid_matches_the_xml_pattern():
    station = SOURCE.station(-2, 1, 1)
    layer = station.super_layers[0].layers[0]
    grid = layer.cells

    assert (grid.count, grid.first_id) == (49, 1)
    assert grid.pitch == pytest.approx(4.2, abs=1e-6)
    assert grid.shape.aabb() == pytest.approx((4.2, 234.8, 1.3), abs=1e-5)


def test_sl2_has_its_own_cell_count():
    """SL2 layers hold 57 cells, not the 49/50/49/48 of SL1 and SL3."""
    station = SOURCE.station(-2, 1, 1)
    sl2 = [sl for sl in station.super_layers if sl.number == 2][0]
    grid = sl2.layers[0].cells

    assert grid.count == 57
    assert grid.offset == pytest.approx(0.0, abs=1e-3)
    assert grid.x_positions()[0] == pytest.approx(-117.6, abs=1e-3)
    assert grid.x_positions()[-1] == pytest.approx(117.6, abs=1e-3)


@pytest.mark.parametrize("chamber", CHAMBERS)
def test_cell_centres_from_specs_match_the_xml(chamber):
    station = SOURCE.station(*chamber)
    expected = SOURCE.cell_centres(*chamber)
    computed = cell_centres(station)

    assert len(computed) == len(expected)
    worst = max(
        float(np.max(np.abs(computed[key] - expected[key]))) for key in expected
    )
    assert worst < 2e-3, "chamber %s: max error %.6f cm" % (chamber, worst)


def test_unknown_chamber_raises():
    with pytest.raises(KeyError, match="chamber"):
        SOURCE.station(9, 9, 9)


def test_specs_do_not_import_xml():
    text = Path(specs.__file__).read_text()

    assert "ElementTree" not in text
    assert "xml" not in text
