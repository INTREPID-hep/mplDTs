"""T-040: the surface DTPatternRecognition imports (ADR-024, ADR-025).

Only what dtpr's plotting modules touch, with no ROOT and no Qt:

    dtpr/utils/dt_plot_functions.py:33-34
    dtpr/utils/gui/artist_gui_manager.py:3
    dtpr/utils/gui/local_plotter.py:110
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pandas import DataFrame

from mpldts.geometry import AMDTSegments, Station, StationsCache, STATION_CACHE
from mpldts.patches import DTRelatedPatch, DTStationPatch, MultiDTSegmentsPatch

CHAMBER = (0, 1, 1)
ROW = {"sl": 1, "l": 1, "w": 2, "time": 400.0}


def test_the_cache_hands_out_shared_geometry_and_overlays():
    cache = StationsCache()
    plain = cache.get(*CHAMBER)
    assert isinstance(plain, Station)
    assert cache.get(*CHAMBER) is plain
    # the names dtpr builds from the station
    assert (plain.wheel, plain.sector, plain.number) == CHAMBER
    assert plain.name

    event = cache.get(*CHAMBER, dt_info=DataFrame([ROW]))
    assert event is not plain
    assert event.super_layer(1).layer(1).cell(2).time == ROW["time"]
    # the cached chamber is never mutated
    assert getattr(plain.super_layer(1).layer(1).cell(2), "time", None) is None


@pytest.mark.parametrize(
    "dt_info",
    [
        dict(ROW),
        [dict(ROW)],
        DataFrame([dict(ROW)]),
    ],
)
def test_the_three_accepted_shapes(dt_info):
    station = STATION_CACHE.get(*CHAMBER, dt_info=dt_info)
    assert station.super_layer(1).layer(1).cell(2).time == ROW["time"]


def test_the_station_patch_draws_both_faces():
    station = STATION_CACHE.get(*CHAMBER)
    figure, axes = plt.subplots(1, 2)
    try:
        for axes_one, faceview in zip(axes, ("phi", "eta")):
            patch = DTStationPatch(
                station, axes_one, faceview=faceview, local=True, vmap="time"
            )
            assert isinstance(patch, DTRelatedPatch)
            assert patch.station is station
            # the GUI manager toggles the artists through this list
            assert len(patch._collections) == 2
    finally:
        plt.close(figure)


def test_a_segment_patch_builds_for_both_faces():
    station = STATION_CACHE.get(*CHAMBER)
    segs_info = [
        {"parent": station, "sl": 1, "position": 10.0, "angle": 5.0, "quality": 3},
        {"parent": station, "sl": 2, "position": -4.0, "angle": 80.0, "quality": 1},
    ]
    for reference_frame in ("Station", "SL13Center"):
        segments = AMDTSegments(segs_info, reference_frame=reference_frame)
        assert np.all(np.isfinite(segments[0].local_center))
        figure, axes = plt.subplots(1, 2)
        try:
            for axes_one, faceview in zip(axes, ("phi", "eta")):
                multi = MultiDTSegmentsPatch(
                    segments=segments,
                    axes=axes_one,
                    local=True,
                    faceview=faceview,
                    vmap="quality",
                )
                assert list(multi.patches) == [CHAMBER]
        finally:
            plt.close(figure)


def test_the_layer_bounds_are_the_cell_ids():
    station = STATION_CACHE.get(*CHAMBER)
    layer = station.super_layer(1).layer(1)
    assert layer.cell(layer._first_cell_id) is not None
    assert layer.cell(layer._last_cell_id) is not None
    assert layer._first_cell_id <= layer._last_cell_id
    cell = layer.cell(layer._first_cell_id)
    assert len(cell.local_center) == 3 and len(cell.global_center) == 3
