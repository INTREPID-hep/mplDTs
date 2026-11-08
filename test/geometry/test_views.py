"""T-030/T-031: a station from a spec draws with the natural views only."""

import numpy as np
import pytest

from mpldts.geometry import Station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import (
    Box,
    CellGrid,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
)

from . import reference

#: A station whose length axis points down the detector z axis (face -1).
LYING = Pose(np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]]))


def _custom(name="custom", pose=None):
    return StationSpec(
        name=name,
        pose=Pose.identity() if pose is None else pose,
        super_layers=[
            SuperLayerSpec(
                number=number,
                pose=Pose.translated(0.0, 0.0, (number - 1) * 12.0),
                layers=[
                    LayerSpec(
                        number=index,
                        pose=Pose.translated(0.0, 0.0, (index - 2.5) * 2.5),
                        cells=CellGrid(pitch=4.0, count=8, shape=Box(4.0, 8.0, 1.3)),
                    )
                    for index in range(1, 5)
                ],
                shape=Box(32.0, 8.0, 8.8),
            )
            for number in (1, 2)
        ],
        shape=Box(32.0, 8.0, 21.0),
    )


def _length_axis(station):
    """The station length axis in the natural phi view: (0, -face, 0)."""
    return station.transformer.transform((0.0, 1.0, 0.0), "StationNvPhi", "Station")


def test_a_custom_station_gets_the_natural_views_only():
    station = Station.from_spec(_custom())

    frames = station.transformer.graph.frames()
    # SectorRef encoded the CMS sector line; it is not a frame of a spec station
    assert not [frame for frame in frames if frame.endswith("SectorRef")]
    assert [frame for frame in frames if frame.endswith("SL13Center")]
    np.testing.assert_allclose(_length_axis(station), (0.0, -1.0, 0.0), atol=1e-12)


def test_sl13_center_is_the_centre_of_the_outermost_super_layers():
    station = Station.from_spec(_custom())

    np.testing.assert_allclose(
        station.transformer.transform((0.0, 0.0, 0.0), "SL13Center", "Station"),
        (0.0, 0.0, 6.0),
        atol=1e-12,
    )


def test_a_mirrored_station_takes_its_face_from_the_pose():
    station = Station.from_spec(_custom("lying", LYING))

    np.testing.assert_allclose(_length_axis(station), (0.0, 1.0, 0.0), atol=1e-12)


def test_a_mirrored_station_still_plots_inverted():
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    from mpldts.patches import DTStationPatch

    station = Station.from_spec(_custom("lying", LYING))
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(station, axes, faceview="phi", local=True, inverted=True)
        assert patch.bounds_collection.get_paths()
        assert patch.cells_collection.get_paths()
    finally:
        plt.close(figure)


def test_the_segments_default_reference_frame_is_a_usable_frame():
    from mpldts.geometry import AMDTSegments

    station = Station.from_spec(_custom(), 0, 1, 1)
    np.testing.assert_allclose(
        station.transformer.transform((0.0, 0.0, 0.0), "SL13Center", "Station"),
        (0.0, 0.0, 6.0),
        atol=1e-12,
    )
    segments = AMDTSegments([{"parent": station, "sl": 1, "position": 10.0, "angle": 5.0}])
    # the segment z is taken from its super layer, so SL1 sits at the station z
    np.testing.assert_allclose(segments[0].local_center, (10.0, 0.0, 0.0), atol=1e-12)


@pytest.mark.parametrize("chamber", reference.REPRESENTATIVE)
def test_a_cms_chamber_takes_its_face_from_its_pose(chamber):
    """The face factor used to be a wheel/sector table; the pose states it now."""
    spec = CMSXMLSource().station(*chamber)
    station = Station.from_spec(spec, *chamber)
    face = 1.0 if spec.pose.rotation[2, 1] >= 0.0 else -1.0

    np.testing.assert_allclose(_length_axis(station), (0.0, -face, 0.0), atol=1e-12)
    for frame in ("StationNvEta", "SL13Center"):
        assert station.transformer.get_transformation(frame, "CMS") is not None
