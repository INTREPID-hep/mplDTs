For an AI agent or a new contributor
====================================

Read ``AGENTS.md`` in the repository root first: the model in one picture, five
rules, recipes and the API cheat sheet. The public objects are listed in
:doc:`../reference/geometry/main` and :doc:`../reference/patches/main`.

.. list-table::
   :header-rows: 1

   * - You want to change
     - Read / edit
     - Verify with
   * - A spec field
     - ``geometry/specs.py``, then ``geometry/serialize.py``; ``geometry/model.py`` only if it is read
     - ``test/test_specs.py`` (JSON round trip)
   * - A hand-written detector
     - ``geometry/constructors.py``
     - ``test/test_examples.py``, ``docs/examples/custom_station.py``
   * - Frames or transforms
     - ``geometry/frames.py``, ``geometry/model.py``
     - ``test/test_frames.py``
   * - CMS XML parsing
     - ``geometry/sources/cms_xml.py``
     - ``test/test_sources.py``; the 250-chamber oracle with ``pytest -m slow``
   * - An exporter
     - ``export/base.py``, copy ``export/tg.py``, ``export/__init__.py``
     - ``test/test_export.py``
   * - A volume name
     - ``export/tg.py`` (``_clean``, ``name_of``) and the Geant4 ``StationSD``
     - ``test/test_export.py``; the C++ decode still reads ``_W``/``_Sec``/``_St``
   * - Per-event drawing
     - ``patches/dt_station_patch.py``
     - ``test/test_patches.py``, ``test/test_downstream_contract.py``
   * - The docs
     - ``docs/``
     - ``cd docs && sphinx-build -b html . _build/html``

Two habits save the next reader: keep specs data (no cached world position, no
per-event value on a node) and never add an import-time XML parse. ``python -m
pytest -q`` runs the default suite; ``-m slow`` adds the CMS oracle.
