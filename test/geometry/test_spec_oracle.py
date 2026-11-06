"""T-012: the spec path reproduces every CMS cell centre."""

import numpy as np
import pytest

from mpldts.geometry.sources import CMSXMLSource

from . import reference
from .spec_centres import cell_centres


@pytest.fixture(scope="module")
def source():
    return CMSXMLSource()


def test_all_chambers_from_the_spec_path(source):
    """The M1 gate: 250 chambers, every cell centre against the XML."""
    failures = []
    worst = 0.0
    for chamber in source.chamber_keys():
        computed = cell_centres(source.station(*chamber))
        expected = source.cell_centres(*chamber)
        for failure in reference.compare_cell_centres(computed, expected):
            failures.append("chamber %s: %s" % (str(chamber), failure))
        worst = max(
            worst,
            max(float(np.max(np.abs(computed[key] - expected[key]))) for key in expected),
        )
    assert not failures, "\n".join(failures[:5])
    assert worst < 2e-3, "max error %.6f cm" % worst


@pytest.mark.parametrize("chamber", reference.REPRESENTATIVE)
def test_representative_chambers_have_the_right_cell_count(source, chamber):
    expected = len(source.cell_centres(*chamber))

    assert len(cell_centres(source.station(*chamber))) == expected
