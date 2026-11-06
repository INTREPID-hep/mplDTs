"""T-030: detector assemblies and stations built from a spec."""

import numpy as np
import pytest

from mpldts.geometry import Station, build_detector
from mpldts.geometry.frames import FrameGraph
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import (
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
)


def _station(name, number_of_super_layers=1, pose=None):
    """A station of 32 x 8 x 8.8 cm super layers, four layers of eight cells."""
    centre = (number_of_super_layers - 1) / 2.0
    super_layers = [
        SuperLayerSpec(
            number=number,
            pose=Pose.translated(0.0, 0.0, (number - 1 - centre) * 9.5),
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
        for number in range(1, number_of_super_layers + 1)
    ]
    return StationSpec(
        name=name,
        pose=Pose.identity() if pose is None else pose,
        super_layers=super_layers,
        shape=Box(32.0, 8.0, (number_of_super_layers - 1) * 9.5 + 8.8),
    )


def _detector():
    return DetectorSpec(
        name="assembly",
        pose=Pose.rotated_z(15.0, (10.0, -20.0, 30.0)),
        stations=[
            _station("A", 1, Pose.rotated_z(30.0, (100.0, 0.0, 0.0))),
            _station("B", 1, Pose.rotated_z(-45.0, (-100.0, 0.0, 10.0))),
        ],
    )


def test_two_stations_build_into_one_detector():
    spec = _detector()
    detector = build_detector(spec)

    assert detector.kind == "detector"
    assert detector.name == "assembly"
    assert [station.name for station in detector.children] == ["A", "B"]
    assert all(station.parent is detector for station in detector.children)

    graph = FrameGraph()
    graph.add_nodes(detector)
    for station, station_spec in zip(detector.children, spec.stations):
        np.testing.assert_allclose(
            station.world_pose.matrix(),
            spec.pose.compose(station_spec.pose).matrix(),
            atol=1e-12,
        )


def test_a_point_through_the_graph_matches_the_composed_pose():
    detector = build_detector(_detector())
    graph = FrameGraph()
    graph.add_nodes(detector)

    point = np.array([1.5, -2.0, 3.0])
    for station in detector.children:
        cell = station.children[0].children[0].children[3]
        np.testing.assert_allclose(
            graph.transform(point, cell.frame_id, "World"),
            cell.world_pose.apply(point),
            atol=1e-12,
        )
        np.testing.assert_allclose(
            graph.transform(cell.world_pose.translation, "World", cell.frame_id),
            (0.0, 0.0, 0.0),
            atol=1e-9,
        )


def test_the_chain_matches_the_spec_poses():
    spec = _detector()
    detector = build_detector(spec)

    station_spec = spec.stations[0]
    super_layer_spec = station_spec.super_layers[0]
    layer_spec = super_layer_spec.layers[0]
    expected = (
        spec.pose.compose(station_spec.pose)
        .compose(super_layer_spec.pose)
        .compose(layer_spec.pose)
        .compose(Pose.translated(layer_spec.cells.x_positions()[3], 0.0, 0.0))
    )
    cell = detector.children[0].children[0].children[0].children[3]
    np.testing.assert_allclose(cell.world_pose.matrix(), expected.matrix(), atol=1e-12)


def test_a_station_builds_from_its_spec():
    station = Station.from_spec(_station("one_sl"))

    assert station.name == "one_sl"
    assert station.bounds == (32.0, 8.8, 8.0)
    assert [super_layer.number for super_layer in station.super_layers] == [1]
    assert len(station.super_layer(1).layers) == 4
    assert len(station.super_layer(1).layer(2).cells) == 8
    assert station.super_layer(1).layer(2).cell(3).id == 3


def test_the_derived_local_centres_agree_with_the_graph():
    station = Station.from_spec(_station("one_sl"))

    np.testing.assert_allclose(
        station.transformer.transform((0.0, 0.0, 0.0), "Station", "CMS"),
        station.global_center,
        atol=1e-12,
    )
    for super_layer in station.super_layers:
        np.testing.assert_allclose(
            super_layer.transformer.transform((0.0, 0.0, 0.0), "SuperLayer", "Station"),
            super_layer.local_center,
            atol=1e-12,
        )
        for layer in super_layer.layers:
            np.testing.assert_allclose(
                layer.transformer.transform((0.0, 0.0, 0.0), "Layer", "Station"),
                layer.local_center,
                atol=1e-12,
            )
            for cell in layer.cells:
                np.testing.assert_allclose(
                    cell.transformer.transform((0.0, 0.0, 0.0), "Cell", "Station"),
                    cell.local_center,
                    atol=1e-12,
                )


def test_a_five_super_layer_station_keeps_every_super_layer():
    spec = _station("five_sl", 5)
    station = Station.from_spec(spec)

    assert [super_layer.number for super_layer in station.super_layers] == [1, 2, 3, 4, 5]
    assert station.super_layer(5).layer(4).cell(8) is not None

    view = Station.from_spec(spec, dt_info=[{"sl": 5, "l": 4, "w": 8, "time": 12.5}])
    assert view.super_layer(5).layer(4).cell(8).time == 12.5
    assert not hasattr(station.super_layer(5).layer(4).cell(8), "time")


def test_a_cms_chamber_through_from_spec_matches_the_cached_view():
    chamber = (-2, 1, 2)
    cached = Station(*chamber)
    built = Station.from_spec(CMSXMLSource().station(*chamber))

    assert [super_layer.number for super_layer in built.super_layers] == [
        super_layer.number for super_layer in cached.super_layers
    ]
    for built_super_layer, cached_super_layer in zip(built.super_layers, cached.super_layers):
        for built_layer, cached_layer in zip(built_super_layer.layers, cached_super_layer.layers):
            assert len(built_layer.cells) == len(cached_layer.cells)
            np.testing.assert_allclose(
                [cell.global_center for cell in built_layer.cells],
                [cell.global_center for cell in cached_layer.cells],
                atol=1e-12,
            )
            # the XML states its positions in single precision
            np.testing.assert_allclose(
                [cell.local_center for cell in built_layer.cells],
                [cell.local_center for cell in cached_layer.cells],
                atol=1e-3,
            )


def test_the_detector_builder_rejects_an_invalid_spec():
    with pytest.raises(ValueError, match="no stations"):
        build_detector(DetectorSpec(name="empty", pose=Pose.identity(), stations=[]))


@pytest.mark.parametrize("number_of_super_layers", [1, 5])
@pytest.mark.parametrize("faceview", ["phi", "eta"])
@pytest.mark.parametrize("local, inverted", [(True, False), (True, True), (False, False)])
def test_custom_stations_plot(number_of_super_layers, faceview, local, inverted):
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    from mpldts.patches import DTStationPatch

    name = "custom_%d" % number_of_super_layers
    station = Station.from_spec(_station(name, number_of_super_layers))
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(station, axes, faceview=faceview, local=local, inverted=inverted)
        assert patch.bounds_collection.get_paths()
        if faceview == "phi":
            assert patch.cells_collection.get_paths()
    finally:
        plt.close(figure)


def test_the_turned_super_layers_are_the_cms_ones():
    pytest.importorskip("matplotlib")
    from mpldts.patches.dt_station_patch import _is_turned

    for chamber in ((-2, 1, 2), (0, 5, 3), (2, 14, 4)):
        station = Station(*chamber)
        assert [_is_turned(super_layer) for super_layer in station.super_layers] == [
            super_layer.number == 2 for super_layer in station.super_layers
        ]


def test_a_turned_super_layer_plots_in_the_eta_view():
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    from mpldts.patches import DTStationPatch
    from mpldts.patches.dt_station_patch import _is_turned

    last = _station("turned", 2)
    turned = SuperLayerSpec(
        number=2,
        pose=Pose.rotated_z(-90.0),
        layers=last.super_layers[1].layers,
        shape=last.super_layers[1].shape,
    )
    spec = StationSpec(
        name="turned",
        pose=Pose.identity(),
        super_layers=[last.super_layers[0], turned],
        shape=last.shape,
    )
    station = Station.from_spec(spec)

    assert not _is_turned(station.super_layer(1))
    assert _is_turned(station.super_layer(2))

    # the cells of a turned super layer are stated in its own plane: the spread
    # runs along the local x and the station z is kept
    cells = station.super_layer(2).layer(1).cells
    np.testing.assert_allclose(
        [cell.local_center[0] for cell in cells],
        spec.super_layers[1].layers[0].cells.x_positions(),
        atol=1e-12,
    )
    np.testing.assert_allclose([cell.local_center[1] for cell in cells], 0.0, atol=1e-12)
    np.testing.assert_allclose([cell.local_center[2] for cell in cells], -3.75, atol=1e-12)

    figure, axes = plt.subplots()
    try:
        phi = DTStationPatch(station, axes, faceview="phi", local=True)
        eta = DTStationPatch(station, axes, faceview="eta", local=True)
        assert len(phi.cells_collection.get_paths()) == 4 * 8
        assert len(eta.cells_collection.get_paths()) == 4 * 8
    finally:
        plt.close(figure)
