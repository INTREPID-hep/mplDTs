"""T-031: the CMS preset owns the CMS-only frames; the face comes from the pose."""

import numpy as np
import pytest

from mpldts.geometry import Station
from mpldts.geometry.presets import cms
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
                number=1,
                pose=Pose.identity(),
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
        ],
        shape=Box(32.0, 8.0, 8.8),
    )


def _length_axis(station):
    """The station length axis in the natural phi view: (0, -face, 0)."""
    return station.transformer.transform((0.0, 1.0, 0.0), "StationNvPhi", "Station")


@pytest.mark.parametrize("chamber", reference.REPRESENTATIVE)
def test_a_cms_chamber_keeps_its_plotting_frames(chamber):
    station = Station(*chamber)
    face = cms.face_factor(chamber[0], chamber[1])

    np.testing.assert_allclose(_length_axis(station), (0.0, -face, 0.0), atol=1e-12)
    for frame in ("StationNvEta", "SectorRef", "SL13Center"):
        assert station.transformer.get_transformation(frame, "CMS") is not None


def test_a_custom_station_gets_the_natural_views_only():
    station = Station.from_spec(_custom())

    frames = station.transformer.graph.frames()
    cms_only = [frame for frame in frames if frame.endswith(("SectorRef", "SL13Center"))]
    assert cms_only == []
    np.testing.assert_allclose(_length_axis(station), (0.0, -1.0, 0.0), atol=1e-12)


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


@pytest.mark.slow
def test_the_face_factor_matches_the_pose_on_every_chamber():
    source = CMSXMLSource()
    for wheel, sector, number in source.chamber_keys():
        station = Station(wheel, sector, number)
        expected = (0.0, -cms.face_factor(wheel, sector), 0.0)
        np.testing.assert_allclose(_length_axis(station), expected, atol=1e-12)
        for frame in ("StationNvEta", "SectorRef", "SL13Center"):
            assert station.transformer.get_transformation(frame, "CMS") is not None, (
                wheel,
                sector,
                number,
                frame,
            )
