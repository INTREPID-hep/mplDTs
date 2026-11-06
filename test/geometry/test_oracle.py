"""T-003: the model must reproduce the XML cell centres and node fields."""

import numpy as np
import pytest

from mpldts.geometry import Station

from . import reference

_CACHE = {}


def _station(chamber):
    """Build each chamber once per session (a station build is ~1 s)."""
    if chamber not in _CACHE:
        _CACHE[chamber] = Station(*chamber)
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


def _compare(chamber, keep_super_layer):
    """Failures for the super layers accepted by the predicate."""
    station = _station(chamber)
    expected = {
        key: value
        for key, value in reference.cell_centres(chamber).items()
        if keep_super_layer(key[0])
    }
    computed = {
        key: value
        for key, value in _computed_cell_centres(station).items()
        if keep_super_layer(key[0])
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
    """Every cell centre matches the XML, except the BUG-01 super layer."""
    failures = _compare(chamber, lambda sl: sl != reference.BUGGY_SUPER_LAYER)
    assert not failures, _report(chamber, failures)


@pytest.mark.parametrize("chamber", reference.REPRESENTATIVE)
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="BUG-01: SL2 pose is wrong by up to 0.5 cm (T-022 fixes it)",
)
def test_sl2_cell_centres_are_known_broken(chamber):
    """SL2 must disagree with the XML until BUG-01 is fixed."""
    if reference.BUGGY_SUPER_LAYER not in reference.super_layer_numbers(chamber):
        pytest.skip("chamber has no SL2")
    failures = _compare(chamber, lambda sl: sl == reference.BUGGY_SUPER_LAYER)
    assert not failures, _report(chamber, failures) + "\n(if SL2 matches now, BUG-01 is fixed: drop the xfail)"


@pytest.mark.parametrize("chamber", reference.REPRESENTATIVE)
def test_node_fields(chamber):
    """Station, super layer and layer fields match the XML."""
    station = _station(chamber)
    expected = reference.node_fields(chamber)

    assert int(station.id) == expected["chamber"]["id"]
    np.testing.assert_allclose(station.local_center, expected["chamber"]["local"], atol=1e-6)
    np.testing.assert_allclose(station.global_center, expected["chamber"]["global"], atol=1e-6)
    np.testing.assert_allclose(station.direction, expected["chamber"]["direction"], atol=1e-6)
    np.testing.assert_allclose(station.bounds, expected["chamber"]["bounds"], atol=1e-6)

    assert sorted(sl.number for sl in station.super_layers) == sorted(expected["super_layers"])
    for sl in station.super_layers:
        node = expected["super_layers"][sl.number]
        np.testing.assert_allclose(sl.local_center, node["local"], atol=1e-6)
        np.testing.assert_allclose(sl.global_center, node["global"], atol=1e-6)
        np.testing.assert_allclose(sl.bounds, node["bounds"], atol=1e-6)
        for layer in sl.layers:
            node = expected["layers"][(sl.number, layer.number)]
            np.testing.assert_allclose(layer.local_center, node["local"], atol=1e-6)
            np.testing.assert_allclose(layer.global_center, node["global"], atol=1e-6)
            np.testing.assert_allclose(layer.bounds, node["bounds"], atol=1e-6)


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
    """All 250 chambers: only SL2 may disagree, and it must disagree."""
    broken = []
    for chamber in reference.all_chambers():
        others = _compare(chamber, lambda sl: sl != reference.BUGGY_SUPER_LAYER)
        if others:
            broken.append(_report(chamber, others))
        has_sl2 = reference.BUGGY_SUPER_LAYER in reference.super_layer_numbers(chamber)
        if has_sl2 and not _compare(chamber, lambda sl: sl == reference.BUGGY_SUPER_LAYER):
            broken.append("chamber %s: SL2 matches the XML, BUG-01 is fixed" % (str(chamber),))
    assert not broken, "\n".join(broken[:5]) + (
        "\n... and %d more chamber(s)" % (len(broken) - 5) if len(broken) > 5 else ""
    )
