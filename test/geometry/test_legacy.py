"""T-022: the legacy wrappers are views over the source, the node tree and the graph."""

from functools import lru_cache

import numpy as np
import pytest

from mpldts.geometry import DriftCell, Layer, Station, SuperLayer
from mpldts.geometry.frames import FrameView

from . import reference

#: A chamber with the three super layers, wheel 0 so the face factor matters.
CHAMBER = (0, 5, 3)


@lru_cache(maxsize=None)
def _station():
    return Station(*CHAMBER)


def test_every_object_is_a_view_on_one_graph():
    station = _station()
    graph = station.transformer.graph
    assert isinstance(station.transformer, FrameView)

    frames = set()
    for super_layer in station.super_layers:
        assert super_layer.transformer.graph is graph
        frames.add(super_layer.transformer.node.frame_id)
        for layer in super_layer.layers:
            assert layer.transformer.graph is graph
            frames.add(layer.transformer.node.frame_id)
            for cell in layer.cells:
                assert cell.transformer.graph is graph
                frames.add(cell.transformer.node.frame_id)

    assert frames <= graph.frames()
    assert len(frames) == 3 * (1 + 4) + sum(len(l.cells) for sl in station.super_layers for l in sl.layers)


def test_standalone_super_layer_and_layer():
    station = _station()
    sl2 = station.super_layer(2)

    standalone = SuperLayer(rawId=sl2.id)
    assert standalone.number == 2
    assert [len(layer.cells) for layer in standalone.layers] == [
        len(layer.cells) for layer in sl2.layers
    ]
    np.testing.assert_allclose(
        standalone.transformer.transform((0, 0, 0), "SL2", "CMS"),
        sl2.transformer.transform((0, 0, 0), "SL2", "CMS"),
        atol=1e-9,
    )

    layer = Layer(rawId=sl2.layers[0].id)
    assert layer.number == 1
    assert isinstance(layer.parent, Station)
    assert len(layer.cells) == len(sl2.layers[0].cells)
    np.testing.assert_allclose(
        layer.transformer.transform(layer.local_center, "Layer", "CMS"),
        sl2.layers[0].transformer.transform(sl2.layers[0].local_center, "Layer", "CMS"),
        atol=1e-9,
    )


def test_a_detached_cell_keeps_its_defaults():
    cell = DriftCell(number=3)

    assert cell.id == 3
    assert cell.number == 3
    assert cell.bounds == (4.2, 1.3, 235)
    assert not hasattr(cell, "transformer")


def test_super_layer_and_sl_names_resolve_to_the_same_frame():
    sl2 = _station().super_layer(2)

    np.testing.assert_allclose(
        sl2.transformer.get_transformation("SuperLayer", "Station"),
        sl2.transformer.get_transformation("SL2", "Station"),
        atol=0.0,
    )


def test_plotting_frames_resolve():
    station = _station()
    for frame in ("StationNvPhi", "StationNvEta", "SectorRef", "SL13Center"):
        assert station.transformer.get_transformation(frame, "CMS") is not None

    rotation = station.transformer.get_transformation("Station", "StationNvPhi")[:3, :3]
    np.testing.assert_allclose(rotation @ rotation.T, np.eye(3), atol=1e-12)

    expected = (
        np.asarray(station.super_layer(1).local_center)
        + np.asarray(station.super_layer(3).local_center)
    ) / 2.0
    np.testing.assert_allclose(
        station.transformer.transform((0, 0, 0), "SL13Center", "Station"), expected, atol=1e-9
    )


def test_plotting_patches_still_build():
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    from mpldts.patches import DTStationPatch

    station = _station()
    for faceview in ("phi", "eta"):
        for local, inverted in ((True, False), (True, True), (False, False)):
            figure, axes = plt.subplots()
            patch = DTStationPatch(
                station, axes, faceview=faceview, local=local, inverted=inverted
            )
            assert patch.bounds_collection.get_paths()
            assert patch.cells_collection.get_paths()
            plt.close(figure)


def test_dt_info_still_reaches_the_cells():
    station = Station(*CHAMBER, dt_info=[{"sl": 1, "l": 1, "w": 1, "time": 300}])

    assert station.super_layer(1).layer(1).cell(1).time == 300


def test_an_unknown_chamber_raises_value_error():
    known = set(reference.all_chambers())
    missing = next(
        (wheel, sector, station)
        for wheel in range(-2, 3)
        for sector in range(1, 15)
        for station in range(1, 5)
        if (wheel, sector, station) not in known
    )

    with pytest.raises(ValueError, match="is not in the CMS geometry"):
        Station(*missing)
