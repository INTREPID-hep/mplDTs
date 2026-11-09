"""T-024/T-070: nothing is parsed at import; one source builds one tree."""

import subprocess
import sys

import numpy as np

from mpldts.geometry import Station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import Box, CellGrid, LayerSpec, Pose, StationSpec, SuperLayerSpec

CHAMBER = (0, 1, 1)


def test_importing_the_library_reads_no_geometry_xml():
    code = (
        "import sys, mpldts.geometry; "
        "assert 'mpldts.geometry.sources.cms_xml' not in sys.modules, 'XML module imported'; "
        "print('lazy')"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "lazy"


def test_one_source_builds_the_same_tree_twice():
    source = CMSXMLSource()
    first = Station.from_spec(source.station(*CHAMBER), *CHAMBER)
    second = Station.from_spec(source.station(*CHAMBER), *CHAMBER)

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
