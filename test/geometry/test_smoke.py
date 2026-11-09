"""T-001/T-070: the geometry package imports, one chamber builds, no shortcuts."""

import mpldts.geometry as geometry
from mpldts.geometry.sources import CMSXMLSource


def test_package_imports():
    assert hasattr(geometry, "Station")
    assert hasattr(geometry, "build_station")


def test_the_removed_shortcuts_are_gone():
    """3.0 deletes the XML wrapper, its lazy proxy and the station cache."""
    for name in ("DTGeometry", "DTGEOMETRY", "StationsCache", "STATION_CACHE"):
        assert not hasattr(geometry, name), name


def test_build_one_station():
    station = geometry.Station.from_spec(CMSXMLSource().station(0, 1, 1), 0, 1, 1)

    assert [sl.number for sl in station.super_layers] == [1, 3, 2]
    assert len(station.super_layer(1).layers) == 4
    assert len(station.super_layer(1).layers[0].cells) == 49
