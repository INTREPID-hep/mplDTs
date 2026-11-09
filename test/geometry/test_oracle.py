"""T-003: the model must reproduce the XML cell centres and node fields."""

import numpy as np
import pytest

from mpldts.geometry import Station
from mpldts.geometry.sources import CMSXMLSource

from . import reference

_CACHE = {}
_SOURCE = None


def _source():
    global _SOURCE
    if _SOURCE is None:
        _SOURCE = CMSXMLSource()
    return _SOURCE


def _station(chamber):
    """Build each chamber once per session (a station build is ~1 s)."""
    if chamber not in _CACHE:
        _CACHE[chamber] = Station.from_spec(_source().station(*chamber), *chamber)
    return _CACHE[chamber]


def _computed_cell_centres(station):
    """{(sl, layer, cell): xyz} from the Cell -> CMS transform."""
    out = {}
    for sl in station.super_layers:
        for layer in sl.layers:
            for cell in layer.cells:
                out[(sl.number, layer.number, cell.number)] = cell.transformer.transform(
                    (0, 0, 0), "Cell", "CMS"
                )
    return out


def _compare(chamber, super_layer=None):
    """Failures for one super layer, or for every super layer when None."""
    station = _station(chamber)
    expected = {
        key: value
        for key, value in reference.cell_centres(chamber).items()
        if super_layer is None or key[0] == super_layer
    }
    computed = {
        key: value
        for key, value in _computed_cell_centres(station).items()
        if super_layer is None or key[0] == super_layer
    }
    return reference.compare_cell_centres(computed, expected)


def _report(chamber, failures, limit=5):
    shown = failures[:limit]
    more = len(failures) - len(shown)
    text = "chamber %s: %d failure(s)" % (str(chamber), len(failures)) + "".join(
        "\n  " + failure for failure in shown
    )
    return text + ("\n  ... and %d more" % more if more else "")


@pytest.mark.parametrize("chamber", reference.REPRESENTATIVE)
def test_cell_centres(chamber):
    """Every cell centre matches the XML, SL2 included."""
    failures = _compare(chamber)
    assert not failures, _report(chamber, failures)


@pytest.mark.parametrize("chamber", reference.REPRESENTATIVE)
def test_sl2_cell_centres(chamber):
    """SL2 used to be off by up to 0.5 cm (BUG-01); it must match the XML now."""
    if reference.SL2 not in reference.super_layer_numbers(chamber):
        pytest.skip("chamber has no SL2")
    failures = _compare(chamber, super_layer=reference.SL2)
    assert not failures, _report(chamber, failures)


@pytest.mark.parametrize("chamber", reference.REPRESENTATIVE)
def test_node_fields(chamber):
    """Station, super layer and layer fields match the XML."""
    station = _station(chamber)
    expected = reference.node_fields(chamber)

    assert station.id == station._node.name
    np.testing.assert_allclose(station.local_center, expected["chamber"]["local"], atol=1e-6)
    np.testing.assert_allclose(station.global_center, expected["chamber"]["global"], atol=1e-6)
    np.testing.assert_allclose(station.direction, expected["chamber"]["direction"], atol=1e-6)
    np.testing.assert_allclose(station.bounds, expected["chamber"]["bounds"], atol=1e-6)

    assert sorted(sl.number for sl in station.super_layers) == sorted(expected["super_layers"])
    for sl in station.super_layers:
        node = expected["super_layers"][sl.number]
        # the XML stores 4 decimals, so the recorded local carries that error too
        np.testing.assert_allclose(sl.local_center, node["local"], atol=2e-3)
        np.testing.assert_allclose(sl.global_center, node["global"], atol=1e-6)
        # a spec super layer has no solid of its own: its box is the union of
        # its children, so it is inside the XML box and it is not empty
        assert 0.0 < sl.bounds[0] <= node["bounds"][0] + 1e-6
        assert 0.0 < sl.bounds[1] <= node["bounds"][1] + 1e-6
        assert 0.0 < sl.bounds[2] <= node["bounds"][2] + 1e-6
        for layer in sl.layers:
            node = expected["layers"][(sl.number, layer.number)]
            np.testing.assert_allclose(layer.local_center, node["local"], atol=2e-3)
            np.testing.assert_allclose(layer.global_center, node["global"], atol=1e-6)
            assert 0.0 < layer.bounds[0] and 0.0 < layer.bounds[1] and 0.0 < layer.bounds[2]


def test_perturbed_reference_is_detected():
    """A 1e-2 cm error must be reported, not swallowed."""
    chamber = reference.REPRESENTATIVE[0]
    expected = reference.cell_centres(chamber)
    key = min(expected)
    expected[key] = expected[key] + np.array([1e-2, 0.0, 0.0])

    failures = reference.compare_cell_centres(_computed_cell_centres(_station(chamber)), expected)

    assert failures, "a 1e-2 cm perturbation was not detected"
    assert "cell sl=" in failures[0]


@pytest.mark.slow
def test_all_chambers():
    """All 250 chambers must match the XML."""
    broken = []
    for chamber in reference.all_chambers():
        failures = _compare(chamber)
        if failures:
            broken.append(_report(chamber, failures))
    assert not broken, "\n".join(broken[:5]) + (
        "\n... and %d more chamber(s)" % (len(broken) - 5) if len(broken) > 5 else ""
    )
