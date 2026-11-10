============
Contributing
============

How to work on the package: run the tests, build the documentation, find the
code, and cut a release. The repository is the source of truth; the prose lives
in ``docs/`` and the library in ``mpldts/``.

Working copy
------------

Work in a branch, keep the runtime dependencies as they are, and do not add a
backend import to ``mpldts.geometry``. The package has three extras: ``test``
(pytest), ``docs`` (Sphinx and the Read the Docs theme) and the formatter. A
change is ready when the test suite is green, the docs build, and the new
behaviour is either a test or a documented example — a snippet in the docs is
executed and its output is the real one.

Tests
-----

Run the suite against the checkout, without installing it over the environment:

.. code-block:: bash

    PYTHONPATH=/home/destrada/mplDTs MPLBACKEND=Agg \
        /home/destrada/Geant4/DTG4Simulator/env/bin/python -m pytest -q

``MPLBACKEND=Agg`` matters: several tests import matplotlib and must not open a
window. The run must be green before a commit.

The ``slow`` marker is deselected by default: ``pyproject.toml`` sets
``addopts = "-m 'not slow'"``. It guards the full 250-chamber oracle, which
takes minutes rather than seconds, and it is the check to run when a change
touches poses, the CMS source or the builder — the fast suite only covers a
representative set of chambers. Select it explicitly with ``-m slow`` on the
oracle module when you need it.

Documentation
-------------

The docs are RST built with Sphinx and the Read the Docs theme; ``docs/conf.py``
reads the version from the package, so there is no separate docs version. Build
them the same way CI does:

.. code-block:: bash

    source /home/destrada/Geant4/DTG4Simulator/env/bin/activate
    cd docs
    sphinx-build -b html . _build/html

The output is ``docs/_build/html/index.html``. A new page is only reachable once
it is listed in a ``toctree``; add it to ``docs/index.rst`` or to the index of
its section. Treat a new warning as a defect — the tree currently builds, and
warnings are how a broken reference or a bad directive survives review.

Code layout
-----------

The geometry is four layers: specs, the node tree, the frame graph, and the
views and exporters that read them. Most changes touch one of these files.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Path
     - What lives there
   * - `geometry/specs.py`
     - Frozen dataclasses: `Pose`, `Box`, `Tube`, `CellGrid`, `LayerSpec`,
       `SuperLayerSpec`, `StationSpec`, `DetectorSpec`, `validate()`.
   * - `geometry/model.py`
     - `Node` and the builders `build_station` and `build_detector`; one
       parent-relative pose per node.
   * - `geometry/frames.py`
     - `FrameGraph` and `FrameView`; path frame ids, scoped aliases and
       virtual frames.
   * - `geometry/*.py`
     - The view layer the patches draw through: `station.py`,
       `super_layer.py`, `layer.py`, `drift_cell.py`, `dt_frame.py`.
   * - `geometry/sources/`
     - `cms_xml.py`: the only place that reads the CMS XML.
   * - `geometry/constructors.py`
     - `make_layer`, `make_superlayer`, `make_station`, `make_detector`.
   * - `geometry/serialize.py`
     - JSON documents `mpldts.station/2` and `mpldts.detector/2`, strict on
       the way in.
   * - `export/`
     - `VolumeSink`, `RecordingSink`, `TgSink` and the placement walk; a
       new format is a new sink here.
   * - `patches/`
     - The matplotlib patches: `DTStationPatch`, `DTObjectsPatch`, the
       segment patches.
   * - `cli.py`
     - `mpldts info|convert|plot`, a thin wrapper over the library.
   * - `test/`
     - `geometry/`, `patches/` and `downstream/`; the last one pins the
       surface the other packages import.

A new field in a spec goes through ``specs.py``, then ``serialize.py`` (the JSON
reader is strict, so the field needs a reader), then ``model.py`` only if the
builder or the graph reads it, and a round-trip test. A new detector follows the
constructors and a documented example. A new backend implements ``VolumeSink``
and is tested through ``RecordingSink``.

Continuous integration
----------------------

Two GitHub Actions workflows run on the repository:

- ``tests`` runs ``pytest -q`` on every push and on every pull request. It runs
  the fast suite only; the ``slow`` oracle is not part of CI.
- ``Sphinx`` builds the documentation on a push to ``main`` that touches
  ``docs/**`` and publishes the result to the ``gh-pages`` branch. Nothing has
  to be deployed by hand.

Release steps
-------------

1. Set the version in ``mpldts/__init__.py`` and in ``pyproject.toml``. The docs
   read the package version, so there is no third copy.
2. Add the new "Version X.Y.Z" section at the top of the changelog. That section
   is the text of the GitHub release, so it says what a user gets, not which
   branch did what.
3. Run the test suite and build the docs. Both downstream packages — the
   pattern-recognition package and the Geant4 simulator — have to be green on
   the candidate tag before it ships; they pin tags, never branches.
4. Create an annotated tag on ``main`` (``vX.Y.Z`` for a release,
   ``vX.Y.Z-beta`` for a prerelease), push the tag together with ``main``.
5. Create the GitHub release from the tag and paste the changelog section as its
   body. A ``-beta`` tag is marked as a prerelease.
6. Move the downstream pins to the new tag and run their suites; a patch release
   only if one of them has to stay on the previous one.

A release is a deletion or a small additive change, never a redesign of the
plotting layer or the volume names in the same window.
