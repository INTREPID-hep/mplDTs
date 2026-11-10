"""The station, object and segment patches."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pandas import DataFrame

from mpldts.geometry import AMDTSegments
from mpldts.patches import DTObjectsPatch, DTSegmentsPatch, DTStationPatch

CHAMBER = (0, 1, 1)
ROW = {"sl": 1, "l": 1, "w": 2, "time": 400.0}


@pytest.fixture(scope="module")
def station(built_station):
    return built_station(CHAMBER)


def _coordinates(line):
    return np.array([line.get_xdata(), line.get_ydata()], dtype=float)


def _drawn(patch):
    return [float(value) for value in np.asarray(patch.cells_collection.get_array())]


# -- the object renderer ---------------------------------------------------


@pytest.mark.parametrize("faceview", ["phi", "eta"])
def test_the_same_line_in_cms_and_station_lands_on_the_same_pixels(station, faceview):
    local = np.array([[0.0, 0.0, 0.0], [30.0, 10.0, 5.0]])
    cms = station.transformer.transform(local, from_frame="Station", to_frame="CMS")
    figure, axes = plt.subplots(1, 2)
    try:
        from_station = DTObjectsPatch(station, axes[0], [(local, {})], faceview=faceview)
        from_cms = DTObjectsPatch(
            station, axes[1], [(cms, {})], frame="CMS", faceview=faceview
        )
        np.testing.assert_allclose(
            _coordinates(from_station.lines[0]),
            _coordinates(from_cms.lines[0]),
            atol=1e-9,
        )
    finally:
        plt.close(figure)


@pytest.mark.parametrize("faceview", ["phi", "eta"])
@pytest.mark.parametrize("super_layer", [1, 2, 3])
def test_a_point_at_a_cell_centre_sits_on_the_cell(station, faceview, super_layer):
    cell = station.super_layer(super_layer).layer(1).cell(5)
    figure, axes = plt.subplots()
    try:
        cells = DTStationPatch(station, axes, faceview=faceview)
        objects = DTObjectsPatch(
            station, axes, [(np.array([cell.local_center]), {})], faceview=faceview
        )
        frame = cells._create_frame(cell)
        centre = frame.get_xy() + np.array([frame.get_width(), frame.get_height()]) / 2
        np.testing.assert_allclose(_coordinates(objects.lines[0])[:, 0], centre, atol=1e-9)
    finally:
        plt.close(figure)


@pytest.mark.parametrize("local, inverted", [(True, True), (False, False)])
def test_the_objects_share_the_transform_of_the_cells(station, local, inverted):
    figure, axes = plt.subplots()
    try:
        # one axes: the two artists are compared through the same transData
        cells = DTStationPatch(station, axes, local=local, inverted=inverted)
        objects = DTObjectsPatch(
            station,
            axes,
            [(np.array([[0.0, 0.0, 0.0]]), {})],
            local=local,
            inverted=inverted,
        )
        np.testing.assert_allclose(
            objects.lines[0].get_transform().get_matrix(),
            cells.cells_collection.get_transform().get_matrix(),
        )
    finally:
        plt.close(figure)


def test_the_segment_paths_stay_as_they_were(station):
    # the 2.5.x output, path for path: the SL2 eta mark is the old one, so
    # dtpr's plots do not move when the segments change
    segments = AMDTSegments(
        [
            {"parent": station, "sl": 1, "position": 10.0, "angle": 5.0, "quality": 3},
            {"parent": station, "sl": 2, "position": -4.0, "angle": 80.0, "quality": 1},
        ]
    )
    expected = {
        "phi": [[[10.321557, 1.788053], [8.578443, 21.711947]]],
        "eta": [[[5.848078, -8.136482], [-13.848078, -4.663518]]],
    }
    for faceview, paths in expected.items():
        figure, axes = plt.subplots()
        try:
            patch = DTSegmentsPatch(
                segments, axes, faceview=faceview, local=True, vmap="quality"
            )
            drawn = [
                [[float(x), float(y)] for x, y in path.vertices]
                for path in patch.segments_collection.get_paths()
            ]
            np.testing.assert_allclose(drawn, paths, atol=1e-6)
        finally:
            plt.close(figure)


def test_a_segment_draws_its_physical_length_when_given(station):
    segments = AMDTSegments(
        [{"parent": station, "sl": 1, "position": 10.0, "angle": 5.0, "length": 7.5}]
    )
    figure, axes = plt.subplots()
    try:
        patch = DTSegmentsPatch(segments, axes, faceview="phi")
        vertices = patch.segments_collection.get_paths()[0].vertices
        assert np.hypot(*(vertices[1] - vertices[0])) == pytest.approx(7.5)
    finally:
        plt.close(figure)


# -- the per-event cell table ----------------------------------------------


def test_one_row_colours_exactly_one_cell(station):
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(station, axes, local=True, vmap="time", data=[dict(ROW)])
        values = _drawn(patch)
        assert values.count(ROW["time"]) == 1
        assert set(values) == {0.0, ROW["time"]}
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "data",
    [dict(ROW), [dict(ROW)], DataFrame([dict(ROW)])],
    ids=["dict", "list", "dataframe"],
)
def test_the_three_accepted_shapes(station, data):
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(station, axes, local=True, vmap="time", data=data)
        assert _drawn(patch).count(ROW["time"]) == 1
    finally:
        plt.close(figure)


def test_float_identifiers_find_their_cell(station):
    """A column read from ROOT or a CSV arrives as a float; (1.0, 1.0, 2.0) is a row."""
    data = DataFrame([{"sl": 1.0, "l": 1.0, "w": 2.0, "time": 12.5}])

    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(station, axes, local=True, vmap="time", data=data)
        assert _drawn(patch).count(12.5) == 1
    finally:
        plt.close(figure)


def test_a_row_without_the_column_is_drawn_at_zero(station):
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(
            station, axes, local=True, vmap="time", data=[{"sl": 1, "l": 1, "w": 2, "energy": 5.0}]
        )
        assert set(_drawn(patch)) == {0.0}
    finally:
        plt.close(figure)


def test_change_vmap_reads_the_new_column(station):
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(
            station,
            axes,
            local=True,
            vmap="time",
            data=[{"sl": 1, "l": 1, "w": 2, "time": 400.0, "energy": 3.5}],
        )
        patch.change_vmap("energy")
        assert max(_drawn(patch)) == 3.5
    finally:
        plt.close(figure)


def test_a_row_without_the_identifiers_is_rejected(station):
    figure, axes = plt.subplots()
    try:
        with pytest.raises(ValueError, match="sl"):
            DTStationPatch(station, axes, data=[{"time": 1.0}])
    finally:
        plt.close(figure)


def test_a_cell_of_an_undrawn_super_layer_keeps_the_other_face(station):
    """phi draws the unturned super layers, eta the turned ones (the CMS SL2)."""
    figure, axes = plt.subplots()
    try:
        patch = DTStationPatch(
            station, axes, faceview="eta", local=True, vmap="time", data=[dict(ROW)]
        )
        assert set(_drawn(patch)) == {0.0}
    finally:
        plt.close(figure)
