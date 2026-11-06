"""Smoke tests: every documented example still runs.

The examples in docs/examples/ are shown verbatim in the Sphinx docs and are
executed here headless, so a runtime change that breaks them breaks the suite.
"""

import runpy
from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402  (after the backend switch)
import pytest  # noqa: E402

EXAMPLES = sorted((Path(__file__).parents[2] / "docs" / "examples").glob("*.py"))


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.stem)
def test_example_runs(example, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # each example saves its figure next to it
    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)
    try:
        runpy.run_path(str(example), run_name="__main__")
    finally:
        plt.close("all")
