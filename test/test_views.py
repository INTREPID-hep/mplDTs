"""The Station view: natural views, attachments and the Station-level oracle."""

import numpy as np
import pytest

from mpldts.geometry import Station, build_station
from mpldts.geometry.specs import (
    AttachmentSpec,
    Box,
    CellGrid,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
)

from .conftest import (
    REPRESENTATIVE,
    SL2,
    all_chambers,
    cell_centres,
    compare_cell_centres,
    station_cell_centres,
    super_layer_numbers,
)

#: A station whose length axis points down the detector z axis (face -1).
LYING = Pose(np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]]))

#: The chamber the simulator uses as its reference for the honeycomb.
CHAMBER = (-2, 1, 2)


def _custom_station(name="custom", pose=None):
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


# -- the natural views -----------------------------------------------------


def test_a_custom_station_gets_the_natural_views_only():
    station = Station.from_spec(_custom_station())

    frames = station.transformer.graph.frames()
    # SectorRef encoded the CMS sector line; it is not a frame of a spec station
    assert not [frame for frame in frames if frame.endswith("SectorRef")]
    assert [frame for frame in frames if frame.endswith("SL13Center")]
    np.testing.assert_allclose(_length_axis(station), (0.0, -1.0, 0.0), atol=1e-12)


def test_sl13_center_is_the_centre_of_the_outermost_super_layers():
    station = Station.from_spec(_custom_station())

    np.testing.assert_allclose(
        station.transformer.transform((0.0, 0.0, 0.0), "SL13Center", "Station"),
        (0.0, 0.0, 6.0),
        atol=1e-12,
    )


def test_a_mirrored_station_takes_its_face_from_the_pose():
    station = Station.from_spec(_custom_station("lying", LYING))

    np.testing.assert_allclose(_length_axis(station), (0.0, 1.0, 0.0), atol=1e-12)


def test_a_mirrored_station_still_plots_inverted():
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    from mpldts.patches import DTStationPatch

    station = Station.from_spec(_custom_station("lying", LYING))
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(station, axes, faceview="phi", local=True, inverted=True)
        assert patch.bounds_collection.get_paths()
        assert patch.cells_collection.get_paths()
    finally:
        plt.close(figure)


def test_the_segments_default_reference_frame_is_a_usable_frame():
    from mpldts.geometry import AMDTSegments

    station = Station.from_spec(_custom_station(), 0, 1, 1)
    np.testing.assert_allclose(
        station.transformer.transform((0.0, 0.0, 0.0), "SL13Center", "Station"),
        (0.0, 0.0, 6.0),
        atol=1e-12,
    )
    segments = AMDTSegments([{"parent": station, "sl": 1, "position": 10.0, "angle": 5.0}])
    # the segment z is taken from its super layer, so SL1 sits at the station z
    np.testing.assert_allclose(segments[0].local_center, (10.0, 0.0, 0.0), atol=1e-12)


@pytest.mark.parametrize("chamber", REPRESENTATIVE)
def test_a_cms_chamber_takes_its_face_from_its_pose(source, chamber):
    """The face factor used to be a wheel/sector table; the pose states it now."""
    spec = source.station(*chamber)
    station = Station.from_spec(spec, *chamber)
    face = 1.0 if spec.pose.rotation[2, 1] >= 0.0 else -1.0

    np.testing.assert_allclose(_length_axis(station), (0.0, -face, 0.0), atol=1e-12)
    for frame in ("StationNvEta", "SL13Center"):
        assert station.transformer.get_transformation(frame, "CMS") is not None


# -- station attachments ---------------------------------------------------


def test_a_cms_chamber_carries_its_honeycomb_panel(built_station):
    panels = built_station(CHAMBER)._node.attachments

    assert [panel.name for panel in panels] == ["Honeycomb"]
    panel = panels[0]
    assert panel.kind == "attachment"
    assert panel.material == "G4_Al"
    # as the simulator builds it: the gap between SL1 and SL2, 1 cm clear
    np.testing.assert_allclose(panel.pose.translation, (0.0, 0.0, 2.67499), atol=1e-3)
    assert panel.shape.dx == pytest.approx(265.799988, abs=1e-3)
    assert panel.shape.dy == pytest.approx(250.100006, abs=1e-3)
    assert panel.shape.dz == pytest.approx(11.80002, abs=1e-3)


def test_the_panel_sits_between_the_super_layers(source, built_station):
    record = source.record(*CHAMBER)
    members = {super_layer["number"]: super_layer for super_layer in record["super_layers"]}
    top = members[1]["local"][2] - members[1]["bounds"][1] / 2.0
    bottom = members[2]["local"][2] + members[2]["bounds"][1] / 2.0

    panel = built_station(CHAMBER)._node.attachments[0]

    assert bottom < panel.pose.translation[2] < top
    assert panel.shape.dz < top - bottom
    assert panel.shape.volume() > 0.0


def test_an_mb4_chamber_takes_the_third_super_layer(source, built_station):
    key = next(chamber for chamber in source.chamber_keys() if chamber[2] == 4)
    record = source.record(*key)
    members = {super_layer["number"]: super_layer for super_layer in record["super_layers"]}
    assert 2 not in members

    panel = built_station(key)._node.attachments[0]
    expected_z = (
        members[3]["local"][2]
        + members[3]["bounds"][1] / 2.0
        + members[1]["local"][2]
        - members[1]["bounds"][1] / 2.0
    ) / 2.0
    np.testing.assert_allclose(panel.pose.translation[2], expected_z, atol=1e-3)


def test_the_panel_is_a_frame(built_station):
    station = built_station(CHAMBER)

    frame = station.transformer.transform((0.0, 0.0, 0.0), "Honeycomb", "Station")
    np.testing.assert_allclose(frame, (0.0, 0.0, 2.67499), atol=1e-3)


def _attachment_station(attachments=()):
    return StationSpec(
        name="custom",
        pose=Pose.identity(),
        super_layers=[
            SuperLayerSpec(
                number=1,
                pose=Pose.identity(),
                layers=[
                    LayerSpec(
                        number=1,
                        pose=Pose.identity(),
                        cells=CellGrid(pitch=4.0, count=8, shape=Box(4.0, 8.0, 1.3)),
                    )
                ],
                shape=None,
            )
        ],
        shape=Box(32.0, 8.0, 8.8),
        attachments=list(attachments),
    )


def test_a_custom_station_carries_only_its_own_attachments():
    panel = AttachmentSpec("Panel", Pose.translated(0.0, 0.0, 5.0), Box(10.0, 10.0, 0.5))
    built = build_station(_attachment_station([panel]))
    station = Station.from_spec(_attachment_station([panel]))

    assert [node.name for node in built.attachments] == ["Panel"]
    assert [node.name for node in station._node.attachments] == ["Panel"]
    np.testing.assert_allclose(
        station._node.attachments[0].pose.translation, (0.0, 0.0, 5.0), atol=1e-12
    )
    assert station._node.frame_id + "/Panel" in station.transformer.graph.frames()


def test_a_custom_station_without_attachments_has_none():
    assert build_station(_attachment_station()).attachments == []
    assert Station.from_spec(_attachment_station())._node.attachments == []


# -- the Station-level oracle ----------------------------------------------


def _compare(station, chamber, super_layer=None):
    """Failures for one super layer, or for every super layer when None."""
    expected = {
        key: value
        for key, value in cell_centres(chamber).items()
        if super_layer is None or key[0] == super_layer
    }
    computed = {
        key: value
        for key, value in station_cell_centres(station).items()
        if super_layer is None or key[0] == super_layer
    }
    return compare_cell_centres(computed, expected)


def _report(chamber, failures, limit=5):
    shown = failures[:limit]
    more = len(failures) - len(shown)
    text = "chamber %s: %d failure(s)" % (str(chamber), len(failures)) + "".join(
        "\n  " + failure for failure in shown
    )
    return text + ("\n  ... and %d more" % more if more else "")


@pytest.mark.parametrize("chamber", REPRESENTATIVE)
def test_cell_centres(built_station, chamber):
    """Every cell centre matches the XML, SL2 included."""
    failures = _compare(built_station(chamber), chamber)
    assert not failures, _report(chamber, failures)


@pytest.mark.parametrize("chamber", REPRESENTATIVE)
def test_sl2_cell_centres(built_station, chamber):
    """SL2 used to be off by up to 0.5 cm (BUG-01); it must match the XML now."""
    if SL2 not in super_layer_numbers(chamber):
        pytest.skip("chamber has no SL2")
    failures = _compare(built_station(chamber), chamber, super_layer=SL2)
    assert not failures, _report(chamber, failures)


@pytest.mark.slow
def test_all_chambers(built_station):
    """All 250 chambers must match the XML."""
    broken = []
    for chamber in all_chambers():
        failures = _compare(built_station(chamber), chamber)
        if failures:
            broken.append(_report(chamber, failures))
    assert not broken, "\n".join(broken[:5]) + (
        "\n... and %d more chamber(s)" % (len(broken) - 5) if len(broken) > 5 else ""
    )
