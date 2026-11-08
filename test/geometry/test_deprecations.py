"""T-074: 2.9.0 names everything 3.0 removes (migration-3.0.md section 1).

The release exists so a consumer can see what it uses before it disappears, so
these checks pin both halves: every legacy call warns once and names its
replacement, and the pipeline that stays says nothing at all.
"""

import io
import warnings

import pytest

from mpldts.export import TgSink, export_volumes
from mpldts.geometry import (
    DTGeometry,
    Layer,
    Station,
    StationsCache,
    SuperLayer,
    build_station,
)
from mpldts.geometry._geometry import _LazyDTGeometry
from mpldts.geometry.sources import CMSXMLSource

#: A chamber with the three super layers, wheel 0 so the face factor matters.
CHAMBER = (0, 5, 3)


def _capture(call):
    """(result, deprecation messages) of a call."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = call()
    messages = []
    for item in caught:
        if issubclass(item.category, DeprecationWarning):
            messages.append(str(item.message))
    return result, messages


def _station():
    return _capture(lambda: Station(*CHAMBER))[0]


def test_the_legacy_chamber_constructor_names_the_pipeline():
    messages = _capture(lambda: Station(*CHAMBER))[1]
    assert len(messages) == 1, messages
    assert messages[0].startswith("Station(wheel, sector, station)")
    assert "build_station" in messages[0]
    assert "Station.from_spec" in messages[0]


def test_per_event_data_names_the_contract_table():
    station = _station()
    info = [{"sl": 1, "l": 1, "w": 1, "time": 300}]

    messages = _capture(lambda: station.set_cell_attrs(info))[1]
    assert len(messages) == 1, messages
    assert "Station.set_cell_attrs" in messages[0]
    assert "ADR-024" in messages[0]

    # the overlay warns once, not twice: the shared body is silent
    messages = _capture(lambda: station.overlay(info))[1]
    assert len(messages) == 1, messages
    assert "Station.overlay" in messages[0]


def test_the_cache_names_the_contract_table():
    cache = StationsCache()
    _capture(lambda: cache.get(*CHAMBER))  # cold: this one also builds the chamber
    messages = _capture(lambda: cache.get(*CHAMBER))[1]
    assert len(messages) == 1, messages
    assert messages[0].startswith("StationsCache.get")


def test_standalone_views_name_the_node_tree():
    super_layer = _station().super_layer(1)

    messages = _capture(lambda: SuperLayer(rawId=super_layer.id))[1]
    assert any(message.startswith("SuperLayer(rawId=...)") for message in messages), messages

    messages = _capture(lambda: Layer(rawId=super_layer.layers[0].id))[1]
    assert any(message.startswith("Layer(rawId=...)") for message in messages), messages


def test_the_xml_reader_names_the_source():
    messages = _capture(lambda: pytest.raises(OSError, DTGeometry, "no-such-file.xml"))[1]
    assert len(messages) == 1, messages
    assert messages[0].startswith("DTGeometry(xml_file)")
    assert "CMSXMLSource" in messages[0]

    lazy = _LazyDTGeometry("no-such-file.xml")
    messages = _capture(lambda: pytest.raises(OSError, getattr, lazy, "root"))[1]
    assert len(messages) == 1, messages
    assert messages[0].startswith("DTGEOMETRY")


def test_the_naming_hook_names_its_replacement():
    messages = _capture(lambda: TgSink(io.StringIO(), name_of=lambda node: None))[1]
    assert len(messages) == 1, messages
    assert messages[0].startswith("TgSink(name_of=...)")
    assert "T-072" in messages[0]


def test_the_surviving_pipeline_is_silent():
    """The guard: the path 3.0 keeps must not warn about itself."""
    source = CMSXMLSource()

    def build():
        spec = source.station(*CHAMBER)
        node = build_station(spec)
        Station.from_spec(spec)
        export_volumes(node, TgSink(io.StringIO()))
        return node

    node, messages = _capture(build)
    assert messages == []
    assert len(node.children) == 3
