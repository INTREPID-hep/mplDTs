"""T-021: the frame graph and the scoped frame views."""

from functools import lru_cache

import numpy as np
import pytest

from mpldts.geometry import FrameGraph, FrameView, build_station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import Pose

from . import reference


@lru_cache(maxsize=None)
def _source():
    return CMSXMLSource()


def _build(chamber):
    station = build_station(_source().station(*chamber))
    graph = FrameGraph()
    graph.add_nodes(station)
    return station, graph


@lru_cache(maxsize=None)
def _cached(chamber):
    return _build(chamber)


def _walk(node):
    yield node
    for child in node.children:
        for descendant in _walk(child):
            yield descendant


def _cell_key(node):
    return (
        int(node.parent.parent.name[2:]),
        int(node.parent.name[1:]),
        int(node.name[1:]),
    )


@pytest.mark.parametrize('chamber', reference.REPRESENTATIVE[:3])
def test_matrix_matches_world_pose(chamber):
    station, graph = _cached(chamber)
    for node in _walk(station):
        pose = graph.matrix(node.frame_id, graph.root)
        assert pose is not None
        np.testing.assert_allclose(pose.matrix(), node.world_pose.matrix(), atol=1e-12)


def test_cell_centres_through_the_view_match_the_xml():
    chamber = reference.REPRESENTATIVE[0]
    station, graph = _cached(chamber)
    expected = _source().cell_centres(*chamber)
    computed = {
        _cell_key(node): FrameView(graph, node).transform([0, 0, 0], 'Cell', 'CMS')
        for node in _walk(station)
        if node.kind == 'cell'
    }
    failures = reference.compare_cell_centres(computed, expected)
    assert not failures, failures[:10]


def test_round_trip_is_the_identity():
    station, graph = _cached(reference.REPRESENTATIVE[1])
    cell = station.children[0].children[0].children[0]
    forward = graph.matrix(cell.frame_id, graph.root)
    backward = graph.matrix(graph.root, cell.frame_id)
    np.testing.assert_allclose(forward.compose(backward).matrix(), np.eye(4), atol=1e-12)
    np.testing.assert_allclose(backward.matrix(), forward.inverse().matrix(), atol=1e-12)


def test_points_get_the_translation_and_vectors_do_not():
    station, graph = _cached(reference.REPRESENTATIVE[2])
    cell = station.children[0].children[0].children[0]
    view = FrameView(graph, cell)
    point = view.transform([0, 0, 0], 'Cell', 'CMS')
    vector = view.transform([0, 0, 0], 'Cell', 'CMS', type='vector')
    np.testing.assert_allclose(point, cell.world_pose.translation)
    np.testing.assert_allclose(vector, np.zeros(3))


def test_sl2_rotation_has_no_special_case():
    chamber = (0, 5, 1) if (0, 5, 1) in _source().chamber_keys() else _source().chamber_keys()[0]
    station, graph = _cached(chamber)
    sl2 = next(node for node in station.children if node.name == 'SL2')
    view = FrameView(graph, sl2.children[0].children[0])
    direction = view.transform([1, 0, 0], 'SL2', 'Station', type='vector')
    np.testing.assert_allclose(direction, [0.0, -1.0, 0.0], atol=1e-12)


def test_aliases_resolve_in_scope():
    station, graph = _cached(reference.REPRESENTATIVE[3])
    sl1 = next(node for node in station.children if node.name == 'SL1')
    cell = sl1.children[0].children[0]
    view = FrameView(graph, cell)

    np.testing.assert_allclose(
        view.transform([0, 0, 0], 'SuperLayer', 'SL1'), np.zeros(3)
    )
    np.testing.assert_allclose(
        view.get_transformation('Layer', 'SL1'),
        graph.get_transformation(cell.parent.frame_id, sl1.frame_id),
    )
    np.testing.assert_allclose(
        FrameView(graph, station).get_transformation('Station', 'CMS'),
        station.pose.matrix(),
    )


def test_unknown_names_raise_keyerror_listing_the_scope():
    station, graph = _cached(reference.REPRESENTATIVE[4])
    view = FrameView(graph, station)
    with pytest.raises(ValueError, match='available'):
        view.transform([0, 0, 0], 'Layer', 'Station')
    with pytest.warns(UserWarning, match='No transformation path'):
        assert view.get_transformation('Nope', 'Station') is None


def test_add_and_remove_a_scoped_frame():
    station, graph = _build(reference.REPRESENTATIVE[5])
    station_view = FrameView(graph, station)
    station_view.add('Station', 'NvPhi', rotation_matrix=Pose.rotated_z(90.0).rotation)

    np.testing.assert_allclose(
        station_view.transform([1, 0, 0], 'Station', 'NvPhi'),
        [0.0, 1.0, 0.0],
        atol=1e-12,
    )
    cell = station.children[0].children[0].children[0]
    np.testing.assert_allclose(
        FrameView(graph, cell).transform([1, 0, 0], 'Station', 'NvPhi'),
        [0.0, 1.0, 0.0],
        atol=1e-12,
    )

    station_view.remove('Station', 'NvPhi')
    with pytest.warns(UserWarning, match='No transformation path'):
        assert FrameView(graph, cell).get_transformation('Station', 'NvPhi') is None


def test_virtual_frames_relative_to_a_node():
    station, graph = _build(reference.REPRESENTATIVE[0])
    graph.add_virtual('SL13Center', station.frame_id, Pose.translated(0.0, 0.0, -5.0))
    cell = station.children[0].children[0].children[0]
    np.testing.assert_allclose(
        FrameView(graph, cell).transform([0, 0, 0], 'SL13Center', 'Station'),
        [0.0, 0.0, -5.0],
    )


def test_no_path_warns_and_returns_none():
    graph = FrameGraph()
    graph.add_edge('/A', graph.root, Pose.identity())
    graph.add_edge('/B', '/Other', Pose.identity())
    with pytest.warns(UserWarning, match='No transformation path'):
        assert graph.get_transformation('/A', '/B') is None
    with pytest.raises(ValueError, match='No transformation path'):
        graph.transform([0, 0, 0], '/A', '/B')


def test_the_cache_is_invalidated_by_an_edge_change():
    graph = FrameGraph()
    graph.add_edge('/A', graph.root, Pose.translated(1.0, 0.0, 0.0))
    np.testing.assert_allclose(graph.transform([0, 0, 0], '/A', graph.root), [1, 0, 0])
    graph.add_edge('/A', graph.root, Pose.translated(2.0, 0.0, 0.0))
    np.testing.assert_allclose(graph.transform([0, 0, 0], '/A', graph.root), [2, 0, 0])
    graph.remove_edge('/A', graph.root)
    assert graph.matrix('/A', graph.root) is None


def test_available_frames_and_str():
    station, graph = _cached(reference.REPRESENTATIVE[1])
    cell = station.children[0].children[0].children[0]
    view = FrameView(graph, cell)
    frames = view.available_frames
    assert station.frame_id in frames
    assert graph.root in frames
    assert str(view).startswith('FrameView:')


def test_the_legacy_station_chain_agrees():
    from mpldts.geometry import Station

    chamber = (0, 5, 3)
    station, graph = _cached(chamber)
    legacy = Station(*chamber).transformer.get_transformation('Station', 'CMS')
    np.testing.assert_allclose(
        graph.get_transformation(station.frame_id, graph.root), legacy, atol=1e-5
    )
