"""The CMS XML source: specs, the lazy import and the spec-path oracle."""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import mpldts.geometry as geometry
from mpldts.geometry import Station
from mpldts.geometry import specs
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import Box, CellGrid, LayerSpec, Pose, StationSpec, SuperLayerSpec

from .conftest import compare_cell_centres, spec_cell_centres

CHAMBERS = [(-2, 1, 1), (0, 1, 1), (2, 14, 4)]
BUILD_CHAMBER = (0, 1, 1)


# -- the CMS XML source ----------------------------------------------------


def test_chamber_index_covers_the_file(source):
    keys = source.chamber_keys()

    assert len(keys) == 250
    assert keys == sorted(keys)
    assert keys[0][0] == -2 and keys[-1][0] == 2


@pytest.mark.parametrize("chamber", CHAMBERS)
def test_station_spec_validates(source, chamber):
    station = source.station(*chamber)

    specs.validate(station)
    assert station.material == "G4_AIR"
    assert [sl.number for sl in station.super_layers] == [1, 3, 2] or len(station.super_layers) == 2


def test_grid_matches_the_xml_pattern(source):
    station = source.station(-2, 1, 1)
    layer = station.super_layers[0].layers[0]
    grid = layer.cells

    assert (grid.count, grid.first_id) == (49, 1)
    assert grid.pitch == pytest.approx(4.2, abs=1e-6)
    assert grid.shape.aabb() == pytest.approx((4.2, 234.8, 1.3), abs=1e-5)


def test_sl2_has_its_own_cell_count(source):
    """SL2 layers hold 57 cells, not the 49/50/49/48 of SL1 and SL3."""
    station = source.station(-2, 1, 1)
    sl2 = [sl for sl in station.super_layers if sl.number == 2][0]
    grid = sl2.layers[0].cells

    assert grid.count == 57
    assert grid.offset == pytest.approx(0.0, abs=1e-3)
    assert grid.x_positions()[0] == pytest.approx(-117.6, abs=1e-3)
    assert grid.x_positions()[-1] == pytest.approx(117.6, abs=1e-3)


def test_unknown_chamber_raises(source):
    with pytest.raises(KeyError, match="chamber"):
        source.station(9, 9, 9)


def test_specs_do_not_import_xml():
    text = Path(specs.__file__).read_text()

    assert "ElementTree" not in text
    assert "xml" not in text


# -- the spec-path oracle --------------------------------------------------


def test_all_chambers_from_the_spec_path(source):
    """The M1 gate: 250 chambers, every cell centre against the XML."""
    failures = []
    worst = 0.0
    for chamber in source.chamber_keys():
        computed = spec_cell_centres(source.station(*chamber))
        expected = source.cell_centres(*chamber)
        for failure in compare_cell_centres(computed, expected):
            failures.append("chamber %s: %s" % (str(chamber), failure))
        worst = max(
            worst,
            max(float(np.max(np.abs(computed[key] - expected[key]))) for key in expected),
        )
    assert not failures, "\n".join(failures[:5])
    assert worst < 2e-3, "max error %.6f cm" % worst


# -- the package surface and its lazy runtime ------------------------------


def test_package_imports():
    assert hasattr(geometry, "Station")
    assert hasattr(geometry, "build_station")


def test_the_removed_shortcuts_are_gone():
    """3.0 deletes the XML wrapper, its lazy proxy and the station cache."""
    for name in ("DTGeometry", "DTGEOMETRY", "StationsCache", "STATION_CACHE"):
        assert not hasattr(geometry, name), name


def test_build_one_station(source):
    station = geometry.Station.from_spec(source.station(0, 1, 1), 0, 1, 1)

    assert [sl.number for sl in station.super_layers] == [1, 3, 2]
    assert len(station.super_layer(1).layers) == 4
    assert len(station.super_layer(1).layers[0].cells) == 49


def test_importing_the_library_reads_no_geometry_xml():
    code = (
        "import sys, mpldts.geometry; "
        "assert 'mpldts.geometry.sources.cms_xml' not in sys.modules, 'XML module imported'; "
        "print('lazy')"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "lazy"


def test_one_source_builds_the_same_tree_twice(source):
    first = Station.from_spec(source.station(*BUILD_CHAMBER), *BUILD_CHAMBER)
    second = Station.from_spec(source.station(*BUILD_CHAMBER), *BUILD_CHAMBER)

    # two views, one geometry: nothing is shared but the values it derives
    assert first is not second
    assert first.local_center == second.local_center
    np.testing.assert_allclose(first.global_center, second.global_center, atol=1e-12)


def _tiny():
    grid = CellGrid(pitch=4.2, count=2, shape=Box(4.2, 40.0, 1.3))
    return StationSpec(
        name="tiny",
        pose=Pose.identity(),
        super_layers=[
            SuperLayerSpec(
                number=1,
                pose=Pose.identity(),
                layers=[LayerSpec(number=1, pose=Pose.identity(), cells=grid)],
                shape=Box(8.4, 40.0, 1.3),
            )
        ],
        shape=Box(8.4, 40.0, 1.3),
    )


def test_a_station_that_is_not_a_cms_chamber_has_no_numbers():
    station = Station.from_spec(_tiny())

    assert (station.wheel, station.sector, station.number) == (None, None, None)
    assert station.name == "tiny"
