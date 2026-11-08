"""T-020: build_station reproduces the spec tree and the CMS cell centres."""

import numpy as np
import pytest

from mpldts.geometry import build_station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import Box, Pose, StationSpec

from . import reference


@pytest.fixture(scope="module")
def source():
    return CMSXMLSource()


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


@pytest.mark.parametrize('chamber', reference.REPRESENTATIVE)
def test_structure_follows_the_spec(source, chamber):
    spec = source.station(*chamber)
    station = build_station(spec)

    assert station.kind == 'station'
    assert station.name == spec.name
    assert [sl.name for sl in station.children] == [
        'SL%d' % sl.number for sl in spec.super_layers
    ]
    for super_layer_node, super_layer_spec in zip(station.children, spec.super_layers):
        assert super_layer_node.kind == 'superlayer'
        assert [node.name for node in super_layer_node.children] == [
            'L%d' % layer.number for layer in super_layer_spec.layers
        ]
        for layer_node, layer_spec in zip(
            super_layer_node.children, super_layer_spec.layers
        ):
            assert layer_node.kind == 'layer'
            assert [node.name for node in layer_node.children] == [
                'C%d' % number for number in layer_spec.cells.ids()
            ]


def test_grouping_nodes_have_no_shape(source):
    spec = source.station(*reference.REPRESENTATIVE[0])
    station = build_station(spec)

    assert isinstance(station.shape, Box)
    assert station.material == spec.material
    for super_layer, layer, cell in _cells(station):
        assert super_layer.shape is None
        assert super_layer.material is None
        assert layer.shape is None
        assert layer.material is None
        assert isinstance(cell.shape, Box)
        # the gas of the cell grid, not of the grouping layer (T-052)
        assert cell.material == "GasMixture"


def test_cells_sit_on_their_grid(source):
    spec = source.station(*reference.REPRESENTATIVE[1])
    station = build_station(spec)

    for super_layer_spec, super_layer_node in zip(spec.super_layers, station.children):
        for layer_spec, layer_node in zip(
            super_layer_spec.layers, super_layer_node.children
        ):
            x = np.array([cell.pose.translation[0] for cell in layer_node.children])
            np.testing.assert_allclose(x, layer_spec.cells.x_positions())
            for cell in layer_node.children:
                np.testing.assert_allclose(cell.pose.translation[1:], (0.0, 0.0))


def test_world_pose_is_the_composition_of_the_poses(source):
    spec = source.station(*reference.REPRESENTATIVE[2])
    station = build_station(spec)

    np.testing.assert_allclose(station.world_pose.matrix(), spec.pose.matrix())
    for super_layer, layer, cell in _cells(station):
        expected = (
            station.world_pose
            .compose(super_layer.pose)
            .compose(layer.pose)
            .compose(cell.pose)
        )
        np.testing.assert_allclose(
            cell.world_pose.matrix(), expected.matrix(), atol=1e-12
        )


def test_frame_ids_are_unique_and_nested(source):
    station = build_station(source.station(*reference.REPRESENTATIVE[3]))
    ids = [station.frame_id]

    def walk(node):
        for child in node.children:
            assert child.frame_id.startswith(node.frame_id + '/')
            assert child.parent is node
            ids.append(child.frame_id)
            walk(child)

    walk(station)
    assert len(ids) == len(set(ids))
    assert station.frame_id.count('/') == 1


def test_a_parent_node_shifts_the_whole_station(source):
    spec = source.station(*reference.REPRESENTATIVE[4])
    outer = build_station(spec)
    inner = build_station(spec, parent=outer)

    assert inner.parent is outer
    np.testing.assert_allclose(
        inner.world_pose.matrix(), outer.world_pose.compose(spec.pose).matrix()
    )
    assert inner.frame_id.startswith(outer.frame_id + '/')


def test_the_builder_rejects_an_invalid_spec():
    with pytest.raises(ValueError, match='no super layers'):
        build_station(
            StationSpec(name='empty', pose=Pose.identity(), super_layers=[])
        )


@pytest.mark.parametrize('chamber', reference.REPRESENTATIVE)
def test_cell_centres_match_the_xml(source, chamber):
    station = build_station(source.station(*chamber))
    failures = reference.compare_cell_centres(
        _centres(station), source.cell_centres(*chamber)
    )
    assert not failures, failures[:10]


@pytest.mark.slow
def test_all_250_chambers_through_the_builder(source):
    failures = []
    for chamber in source.chamber_keys():
        station = build_station(source.station(*chamber))
        for failure in reference.compare_cell_centres(
            _centres(station), source.cell_centres(*chamber)
        ):
            failures.append('chamber %s: %s' % (chamber, failure))
    assert not failures, failures[:5]
