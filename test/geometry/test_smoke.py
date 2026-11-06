"""T-001: the geometry package imports and one chamber builds."""

import mpldts.geometry as geometry


def test_package_imports():
    assert hasattr(geometry, "Station")
    assert hasattr(geometry, "DTGEOMETRY")


def test_build_one_station():
    station = geometry.Station(0, 1, 1)

    assert int(station.id) == 574980096
    assert [sl.number for sl in station.super_layers] == [1, 3, 2]
    assert len(station.super_layer(1).layers) == 4
    assert len(station.super_layer(1).layers[0].cells) == 49
