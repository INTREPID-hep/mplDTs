"""T-071: the (sl, l, w) cell table is the only per-event path."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pandas import DataFrame

from mpldts.geometry import Station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.patches import DTStationPatch

CHAMBER = (0, 1, 1)
ROW = {"sl": 1, "l": 1, "w": 2, "time": 400.0}


@pytest.fixture(scope="module")
def station():
    return Station.from_spec(CMSXMLSource().station(*CHAMBER), *CHAMBER)


def _drawn(patch):
    return [float(value) for value in np.asarray(patch.cells_collection.get_array())]


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


def test_two_events_draw_on_one_station_without_seeing_each_other(station):
    figure, axes = plt.subplots(1, 2)
    try:
        first = DTStationPatch(station, axes[0], local=True, vmap="time", data=[dict(ROW)])
        second = DTStationPatch(
            station,
            axes[1],
            local=True,
            vmap="time",
            data=[{"sl": 1, "l": 1, "w": 2, "time": 900.0}],
        )
        assert max(_drawn(first)) == ROW["time"]
        assert max(_drawn(second)) == 900.0
        assert not hasattr(station.super_layer(1).layer(1).cell(2), "time")
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
