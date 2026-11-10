"""The surface DTPatternRecognition imports (ADR-024, ADR-025).

Only what dtpr's plotting modules touch, with no ROOT and no Qt:

    dtpr/utils/dt_plot_functions.py
    dtpr/utils/gui/artist_gui_manager.py
    dtpr/utils/gui/local_plotter.py
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pandas import DataFrame

from mpldts.geometry import AMDTSegments
from mpldts.patches import DTRelatedPatch, DTStationPatch, MultiDTSegmentsPatch

CHAMBER = (0, 1, 1)
ROW = {"sl": 1, "l": 1, "w": 2, "time": 400.0}


@pytest.fixture(scope="module")
def station(built_station):
    """What dtpr builds: a source, a spec, and a view carrying the chamber numbers."""
    return built_station(CHAMBER)


def test_the_station_carries_the_numbers_dtpr_labels_plots_with(station):
    assert (station.wheel, station.sector, station.number) == CHAMBER
    assert station.name == "W0_S1_MB1"


def test_the_table_is_the_only_per_event_path(station):
    """One station, two events: the geometry is never mutated (ADR-024)."""
    figure, axes = plt.subplots(1, 2)
    try:
        first = DTStationPatch(station, axes[0], local=True, vmap="time", data=DataFrame([ROW]))
        second = DTStationPatch(
            station,
            axes[1],
            local=True,
            vmap="time",
            data=[{"sl": 1, "l": 1, "w": 2, "time": 900.0}],
        )
        assert max(first.cells_collection.get_array()) == ROW["time"]
        assert max(second.cells_collection.get_array()) == 900.0
        # nothing was written on the geometry the two patches share
        assert not hasattr(station.super_layer(1).layer(1).cell(2), "time")
    finally:
        plt.close(figure)


def test_the_station_patch_draws_both_faces(station):
    figure, axes = plt.subplots(1, 2)
    try:
        for axes_one, faceview in zip(axes, ("phi", "eta")):
            patch = DTStationPatch(
                station, axes_one, faceview=faceview, local=True, vmap="time", data=DataFrame([ROW])
            )
            assert isinstance(patch, DTRelatedPatch)
            assert patch.station is station
            # the GUI manager toggles the artists through this list
            assert len(patch._collections) == 2
    finally:
        plt.close(figure)


def test_a_segment_patch_builds_for_both_faces(station):
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


def test_the_layer_bounds_are_the_cell_ids(station):
    layer = station.super_layer(1).layer(1)
    assert layer.cell(layer._first_cell_id) is not None
    assert layer.cell(layer._last_cell_id) is not None
    assert layer._first_cell_id <= layer._last_cell_id
    cell = layer.cell(layer._first_cell_id)
    assert len(cell.local_center) == 3 and len(cell.global_center) == 3
