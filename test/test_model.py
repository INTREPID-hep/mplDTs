"""build_station / build_detector and the Node tree they produce."""

import numpy as np
import pytest

from mpldts.geometry import Station, build_detector, build_station
from mpldts.geometry.frames import FrameGraph
from mpldts.geometry.specs import (
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    StructureSpec,
    SuperLayerSpec,
    validate,
)

from .conftest import (
    REPRESENTATIVE,
    cell_centres,
    compare_cell_centres,
    node_fields,
    station_cell_centres,
)


# -- the node tree ---------------------------------------------------------


def _cells(station):
    for super_layer in station.children:
        for layer in super_layer.children:
            for cell in layer.children:
                yield super_layer, layer, cell


def _centres(station):
    return {
        (int(sl.name[2:]), int(layer.name[1:]), int(cell.name[1:])): cell.world_pose.translation
        for sl, layer, cell in _cells(station)
    }


@pytest.mark.parametrize("chamber", REPRESENTATIVE)
def test_structure_follows_the_spec(source, chamber):
    spec = source.station(*chamber)
    station = build_station(spec)

    assert station.kind == "station"
    assert station.name == spec.name
    assert [sl.name for sl in station.children] == ["SL%d" % sl.number for sl in spec.super_layers]
    for super_layer_node, super_layer_spec in zip(station.children, spec.super_layers):
        assert super_layer_node.kind == "superlayer"
        assert [node.name for node in super_layer_node.children] == [
            "L%d" % layer.number for layer in super_layer_spec.layers
        ]
        for layer_node, layer_spec in zip(super_layer_node.children, super_layer_spec.layers):
            assert layer_node.kind == "layer"
            assert [node.name for node in layer_node.children] == [
                "C%d" % number for number in layer_spec.cells.ids()
            ]


def test_grouping_nodes_have_no_shape(source):
    spec = source.station(*REPRESENTATIVE[0])
    station = build_station(spec)

    assert isinstance(station.shape, Box)
    assert station.material == spec.material
    for super_layer, layer, cell in _cells(station):
        assert super_layer.shape is None
        assert super_layer.material is None
        assert layer.shape is None
        assert layer.material is None
        assert isinstance(cell.shape, Box)
        # the gas of the cell grid, not of the grouping layer
        assert cell.material == "GasMixture"


def test_cells_sit_on_their_grid(source):
    spec = source.station(*REPRESENTATIVE[1])
    station = build_station(spec)

    for super_layer_spec, super_layer_node in zip(spec.super_layers, station.children):
        for layer_spec, layer_node in zip(super_layer_spec.layers, super_layer_node.children):
            x = np.array([cell.pose.translation[0] for cell in layer_node.children])
            np.testing.assert_allclose(x, layer_spec.cells.x_positions())
            for cell in layer_node.children:
                np.testing.assert_allclose(cell.pose.translation[1:], (0.0, 0.0))


def test_world_pose_is_the_composition_of_the_poses(source):
    spec = source.station(*REPRESENTATIVE[2])
    station = build_station(spec)

    np.testing.assert_allclose(station.world_pose.matrix(), spec.pose.matrix())
    for super_layer, layer, cell in _cells(station):
        expected = station.world_pose.compose(super_layer.pose).compose(layer.pose).compose(cell.pose)
        np.testing.assert_allclose(cell.world_pose.matrix(), expected.matrix(), atol=1e-12)


def test_frame_ids_are_unique_and_nested(source):
    station = build_station(source.station(*REPRESENTATIVE[3]))
    ids = [station.frame_id]

    def walk(node):
        for child in node.children:
            assert child.frame_id.startswith(node.frame_id + "/")
            assert child.parent is node
            ids.append(child.frame_id)
            walk(child)

    walk(station)
    assert len(ids) == len(set(ids))
    assert station.frame_id.count("/") == 1


def test_a_parent_node_shifts_the_whole_station(source):
    spec = source.station(*REPRESENTATIVE[4])
    outer = build_station(spec)
    inner = build_station(spec, parent=outer)

    assert inner.parent is outer
    np.testing.assert_allclose(
        inner.world_pose.matrix(), outer.world_pose.compose(spec.pose).matrix()
    )
    assert inner.frame_id.startswith(outer.frame_id + "/")


def test_the_station_builder_rejects_an_invalid_spec():
    with pytest.raises(ValueError, match="no super layers"):
        build_station(StationSpec(name="empty", pose=Pose.identity(), super_layers=[]))


@pytest.mark.parametrize("chamber", REPRESENTATIVE)
def test_cell_centres_match_the_xml(source, chamber):
    station = build_station(source.station(*chamber))
    failures = compare_cell_centres(_centres(station), source.cell_centres(*chamber))
    assert not failures, failures[:10]


@pytest.mark.slow
def test_all_250_chambers_through_the_builder(source):
    failures = []
    for chamber in source.chamber_keys():
        station = build_station(source.station(*chamber))
        for failure in compare_cell_centres(
            _centres(station), source.cell_centres(*chamber)
        ):
            failures.append("chamber %s: %s" % (chamber, failure))
    assert not failures, failures[:5]


# -- the node fields -------------------------------------------------------


@pytest.mark.parametrize("chamber", REPRESENTATIVE)
def test_node_fields(built_station, chamber):
    """Station, super layer and layer fields match the XML."""
    station = built_station(chamber)
    expected = node_fields(chamber)

    assert station.id == station._node.name
    np.testing.assert_allclose(station.local_center, expected["chamber"]["local"], atol=1e-6)
    np.testing.assert_allclose(station.global_center, expected["chamber"]["global"], atol=1e-6)
    np.testing.assert_allclose(station.direction, expected["chamber"]["direction"], atol=1e-6)
    np.testing.assert_allclose(station.bounds, expected["chamber"]["bounds"], atol=1e-6)

    assert sorted(sl.number for sl in station.super_layers) == sorted(expected["super_layers"])
    for sl in station.super_layers:
        node = expected["super_layers"][sl.number]
        # the XML stores 4 decimals, so the recorded local carries that error too
        np.testing.assert_allclose(sl.local_center, node["local"], atol=2e-3)
        np.testing.assert_allclose(sl.global_center, node["global"], atol=1e-6)
        # a spec super layer has no solid of its own: its box is the union of
        # its children, so it is inside the XML box and it is not empty
        assert 0.0 < sl.bounds[0] <= node["bounds"][0] + 1e-6
        assert 0.0 < sl.bounds[1] <= node["bounds"][1] + 1e-6
        assert 0.0 < sl.bounds[2] <= node["bounds"][2] + 1e-6
        for layer in sl.layers:
            node = expected["layers"][(sl.number, layer.number)]
            np.testing.assert_allclose(layer.local_center, node["local"], atol=2e-3)
            np.testing.assert_allclose(layer.global_center, node["global"], atol=1e-6)
            assert 0.0 < layer.bounds[0] and 0.0 < layer.bounds[1] and 0.0 < layer.bounds[2]


def test_perturbed_reference_is_detected(built_station):
    """A 1e-2 cm error must be reported, not swallowed."""
    chamber = REPRESENTATIVE[0]
    expected = cell_centres(chamber)
    key = min(expected)
    expected[key] = expected[key] + np.array([1e-2, 0.0, 0.0])

    failures = compare_cell_centres(station_cell_centres(built_station(chamber)), expected)

    assert failures, "a 1e-2 cm perturbation was not detected"
    assert "cell sl=" in failures[0]


# -- detector assemblies ---------------------------------------------------


def _assembly_station(name, number_of_super_layers=1, pose=None):
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


def _assembly_detector():
    return DetectorSpec(
        name="assembly",
        pose=Pose.rotated_z(15.0, (10.0, -20.0, 30.0)),
        stations=[
            _assembly_station("A", 1, Pose.rotated_z(30.0, (100.0, 0.0, 0.0))),
            _assembly_station("B", 1, Pose.rotated_z(-45.0, (-100.0, 0.0, 10.0))),
        ],
    )


def test_two_stations_build_into_one_detector():
    spec = _assembly_detector()
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
    detector = build_detector(_assembly_detector())
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
    spec = _assembly_detector()
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
    station = Station.from_spec(_assembly_station("one_sl"))

    assert station.name == "one_sl"
    assert station.bounds == (32.0, 8.8, 8.0)
    assert [super_layer.number for super_layer in station.super_layers] == [1]
    assert len(station.super_layer(1).layers) == 4
    assert len(station.super_layer(1).layer(2).cells) == 8
    assert station.super_layer(1).layer(2).cell(3).id == 3


def test_the_derived_local_centres_agree_with_the_graph():
    station = Station.from_spec(_assembly_station("one_sl"))

    np.testing.assert_allclose(
        station.transformer.transform((0.0, 0.0, 0.0), "Station", "CMS"),
        station.global_center,
        atol=1e-12,
    )
    for super_layer in station.super_layers:
        np.testing.assert_allclose(
            super_layer.transformer.transform(
                (0.0, 0.0, 0.0), "SL%d" % super_layer.number, "Station"
            ),
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
    spec = _assembly_station("five_sl", 5)
    station = Station.from_spec(spec)

    assert [super_layer.number for super_layer in station.super_layers] == [1, 2, 3, 4, 5]
    assert station.super_layer(5).layer(4).cell(8) is not None


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
    station = Station.from_spec(_assembly_station(name, number_of_super_layers))
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(station, axes, faceview=faceview, local=local, inverted=inverted)
        assert patch.bounds_collection.get_paths()
        if faceview == "phi":
            assert patch.cells_collection.get_paths()
    finally:
        plt.close(figure)


def test_the_turned_super_layers_are_the_cms_ones(source):
    pytest.importorskip("matplotlib")
    from mpldts.patches.dt_station_patch import _is_turned

    for chamber in ((-2, 1, 2), (0, 5, 3), (2, 14, 4)):
        station = Station.from_spec(source.station(*chamber), *chamber)
        assert [_is_turned(super_layer) for super_layer in station.super_layers] == [
            super_layer.number == 2 for super_layer in station.super_layers
        ]


def test_a_turned_super_layer_plots_in_the_eta_view():
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    from mpldts.patches import DTStationPatch
    from mpldts.patches.dt_station_patch import _is_turned

    last = _assembly_station("turned", 2)
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


# -- passive stations and detector structure -------------------------------


def _passive_wall(name="LeadWall", material="G4_Pb", z=0.0):
    return StationSpec(
        name=name,
        pose=Pose.translated(0.0, 0.0, z),
        super_layers=[],
        shape=Box(100.0, 100.0, 5.0),
        material=material,
    )


def test_a_station_without_super_layers_but_with_a_solid_is_a_station_node():
    node = build_station(_passive_wall())

    assert node.kind == "station"
    assert node.children == []
    assert node.shape.aabb() == (100.0, 100.0, 5.0)
    assert node.material == "G4_Pb"


def test_the_view_of_a_passive_volume_has_no_super_layers():
    station = Station.from_spec(_passive_wall())

    assert station.super_layers == []
    assert station.bounds[0] == pytest.approx(100.0)
    assert station.bounds[1] == pytest.approx(5.0)


def test_a_passive_volume_sits_in_its_detector():
    detector = DetectorSpec(
        name="MuTel",
        pose=Pose.identity(),
        stations=[_passive_wall(z=-27.0), _passive_wall("LeadWall2", z=27.0)],
        shape=Box(120.0, 120.0, 80.0),
    )

    node = build_detector(detector)

    assert [child.name for child in node.children] == ["LeadWall", "LeadWall2"]
    np.testing.assert_allclose(
        [child.world_pose.translation[2] for child in node.children], [-27.0, 27.0], atol=1e-12
    )


def _structure_station(name="MB"):
    return StationSpec(
        name=name,
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
            )
        ],
        shape=Box(32.0, 8.0, 8.8),
    )


def _structure_detector(structure=()):
    return DetectorSpec(
        name="detector",
        pose=Pose.identity(),
        stations=[_structure_station()],
        structure=list(structure),
    )


def _node_names(node):
    found = [node.name]
    for child in list(node.children) + list(node.attachments):
        found.extend(_node_names(child))
    return found


def test_structure_validates_and_builds_no_node():
    yoke = StructureSpec("Yoke", Pose.translated(0.0, 0.0, -100.0), Box(100.0, 100.0, 200.0))
    spec = _structure_detector([yoke])

    validate(spec)
    detector = build_detector(spec)

    assert yoke.material == "G4_Fe"
    assert [node.name for node in detector.children] == ["MB"]
    assert detector.attachments == []
    assert "Yoke" not in _node_names(detector)


def test_a_detector_without_structure_is_unchanged():
    spec = _structure_detector()

    assert spec.structure == []
    assert [node.name for node in build_detector(spec).children] == ["MB"]
