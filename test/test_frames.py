"""The frame graph and the scoped frame views."""

from functools import lru_cache

import numpy as np
import pytest

from mpldts.geometry import FrameGraph, FrameView, Station, build_station
from mpldts.geometry.specs import Pose

from .conftest import REPRESENTATIVE, compare_cell_centres


def _build(source, chamber):
    station = build_station(source.station(*chamber))
    graph = FrameGraph()
    graph.add_nodes(station)
    return station, graph


@lru_cache(maxsize=None)
def _cached(source, chamber):
    return _build(source, chamber)


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


@pytest.mark.parametrize("chamber", REPRESENTATIVE[:3])
def test_matrix_matches_world_pose(source, chamber):
    station, graph = _cached(source, chamber)
    for node in _walk(station):
        pose = graph.matrix(node.frame_id, graph.root)
        assert pose is not None
        np.testing.assert_allclose(pose.matrix(), node.world_pose.matrix(), atol=1e-12)


def test_cell_centres_through_the_view_match_the_xml(source):
    chamber = REPRESENTATIVE[0]
    station, graph = _cached(source, chamber)
    expected = source.cell_centres(*chamber)
    computed = {
        _cell_key(node): FrameView(graph, node).transform([0, 0, 0], "Cell", "CMS")
        for node in _walk(station)
        if node.kind == "cell"
    }
    failures = compare_cell_centres(computed, expected)
    assert not failures, failures[:10]


def test_round_trip_is_the_identity(source):
    station, graph = _cached(source, REPRESENTATIVE[1])
    cell = station.children[0].children[0].children[0]
    forward = graph.matrix(cell.frame_id, graph.root)
    backward = graph.matrix(graph.root, cell.frame_id)
    np.testing.assert_allclose(forward.compose(backward).matrix(), np.eye(4), atol=1e-12)
    np.testing.assert_allclose(backward.matrix(), forward.inverse().matrix(), atol=1e-12)


def test_points_get_the_translation_and_vectors_do_not(source):
    station, graph = _cached(source, REPRESENTATIVE[2])
    cell = station.children[0].children[0].children[0]
    view = FrameView(graph, cell)
    point = view.transform([0, 0, 0], "Cell", "CMS")
    vector = view.transform([0, 0, 0], "Cell", "CMS", type="vector")
    np.testing.assert_allclose(point, cell.world_pose.translation)
    np.testing.assert_allclose(vector, np.zeros(3))


def test_sl2_rotation_has_no_special_case(source):
    chamber = (0, 5, 1) if (0, 5, 1) in source.chamber_keys() else source.chamber_keys()[0]
    station, graph = _cached(source, chamber)
    sl2 = next(node for node in station.children if node.name == "SL2")
    view = FrameView(graph, sl2.children[0].children[0])
    direction = view.transform([1, 0, 0], "SL2", "Station", type="vector")
    np.testing.assert_allclose(direction, [0.0, -1.0, 0.0], atol=1e-12)


def test_aliases_resolve_in_scope(source):
    station, graph = _cached(source, REPRESENTATIVE[3])
    sl1 = next(node for node in station.children if node.name == "SL1")
    cell = sl1.children[0].children[0]
    view = FrameView(graph, cell)

    # "SuperLayer" was a 2.x alias for the nearest super layer; 3.0 drops it
    with pytest.raises(ValueError, match="not a frame"):
        view.transform([0, 0, 0], "SuperLayer", "SL1")
    np.testing.assert_allclose(
        view.get_transformation("Layer", "SL1"),
        graph.get_transformation(cell.parent.frame_id, sl1.frame_id),
    )
    np.testing.assert_allclose(
        FrameView(graph, station).get_transformation("Station", "CMS"),
        station.pose.matrix(),
    )


def test_unknown_names_raise_keyerror_listing_the_scope(source):
    station, graph = _cached(source, REPRESENTATIVE[4])
    view = FrameView(graph, station)
    with pytest.raises(ValueError, match="available"):
        view.transform([0, 0, 0], "Layer", "Station")
    with pytest.warns(UserWarning, match="No transformation path"):
        assert view.get_transformation("Nope", "Station") is None


def test_add_and_remove_a_scoped_frame(source):
    station, graph = _build(source, REPRESENTATIVE[5])
    station_view = FrameView(graph, station)
    station_view.add("Station", "NvPhi", rotation_matrix=Pose.rotated_z(90.0).rotation)

    np.testing.assert_allclose(
        station_view.transform([1, 0, 0], "Station", "NvPhi"),
        [0.0, 1.0, 0.0],
        atol=1e-12,
    )
    cell = station.children[0].children[0].children[0]
    np.testing.assert_allclose(
        FrameView(graph, cell).transform([1, 0, 0], "Station", "NvPhi"),
        [0.0, 1.0, 0.0],
        atol=1e-12,
    )

    station_view.remove("Station", "NvPhi")
    with pytest.warns(UserWarning, match="No transformation path"):
        assert FrameView(graph, cell).get_transformation("Station", "NvPhi") is None


def test_virtual_frames_relative_to_a_node(source):
    station, graph = _build(source, REPRESENTATIVE[0])
    graph.add_virtual("SL13Center", station.frame_id, Pose.translated(0.0, 0.0, -5.0))
    cell = station.children[0].children[0].children[0]
    np.testing.assert_allclose(
        FrameView(graph, cell).transform([0, 0, 0], "SL13Center", "Station"),
        [0.0, 0.0, -5.0],
    )


def test_no_path_warns_and_returns_none():
    graph = FrameGraph()
    graph.add_edge("/A", graph.root, Pose.identity())
    graph.add_edge("/B", "/Other", Pose.identity())
    with pytest.warns(UserWarning, match="No transformation path"):
        assert graph.get_transformation("/A", "/B") is None
    with pytest.raises(ValueError, match="No transformation path"):
        graph.transform([0, 0, 0], "/A", "/B")


def test_the_cache_is_invalidated_by_an_edge_change():
    graph = FrameGraph()
    graph.add_edge("/A", graph.root, Pose.translated(1.0, 0.0, 0.0))
    np.testing.assert_allclose(graph.transform([0, 0, 0], "/A", graph.root), [1, 0, 0])
    graph.add_edge("/A", graph.root, Pose.translated(2.0, 0.0, 0.0))
    np.testing.assert_allclose(graph.transform([0, 0, 0], "/A", graph.root), [2, 0, 0])
    graph.remove_edge("/A", graph.root)
    assert graph.matrix("/A", graph.root) is None


def test_available_frames_and_str(source):
    station, graph = _cached(source, REPRESENTATIVE[1])
    cell = station.children[0].children[0].children[0]
    view = FrameView(graph, cell)
    frames = view.available_frames
    assert station.frame_id in frames
    assert graph.root in frames
    assert str(view).startswith("FrameView:")


def test_available_frames_keeps_the_legacy_names(source):
    # AMDTSegment checks the reference frame here before transforming, so the
    # names must be members, not only their ids. Use the station's own view:
    # the virtual frames live in the graph the constructor builds.
    chamber = REPRESENTATIVE[1]
    view = Station.from_spec(source.station(*chamber), *chamber).transformer
    frames = view.available_frames
    for name in (
        "Station",
        "CMS",
        "World",
        "SL1",
        "SL2",
        "SL3",
        "StationNvPhi",
        "StationNvEta",
        "SL13Center",
    ):
        assert name in frames, name
    # SectorRef was a CMS-sector frame; 3.0 does not register it
    assert "SectorRef" not in frames
    assert view.graph.root in frames


def test_am_segments_build_from_the_legacy_reference_frames(source):
    from mpldts.geometry import AMDTSegments

    chamber = REPRESENTATIVE[1]
    station = Station.from_spec(source.station(*chamber), *chamber)
    for frame in ("Station", "SL13Center", "SL1"):
        segments = AMDTSegments(
            [{"parent": station, "sl": 1, "position": 10.0, "angle": 5.0}],
            reference_frame=frame,
        )
        assert np.all(np.isfinite(segments[0].local_center)), frame
        assert np.all(np.isfinite(segments[0].global_center)), frame


def test_the_station_frame_is_the_xml_global_position(source):
    """One way to build a station: the graph and the view must agree on it."""
    chamber = (0, 5, 3)
    station, graph = _cached(source, chamber)
    view = Station.from_spec(source.station(*chamber), *chamber)
    np.testing.assert_allclose(
        graph.get_transformation(station.frame_id, graph.root)[0:3, 3],
        view.global_center,
        atol=1e-5,
    )
