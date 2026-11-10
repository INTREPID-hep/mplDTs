Use mplDTs from another package
===============================

The reference downstream is ``DTPatternRecognition`` (dtpr): it builds the
chamber view once and redraws it per event. ``test/test_downstream_contract.py``
pins the surface it imports.

The per-event contract
----------------------

.. code-block:: python

   import matplotlib
   matplotlib.use("Agg")
   import matplotlib.pyplot as plt

   from mpldts.geometry import Station
   from mpldts.geometry.sources import CMSXMLSource
   from mpldts.patches import DTStationPatch

   rows = [
       {"sl": 1, "l": 1, "w": 1, "time": 350.0, "energy": 1.2},
       {"sl": 3, "l": 2, "w": 2, "time": 410.0, "energy": 0.7},
   ]
   station = Station.from_spec(CMSXMLSource().station(-2, 1, 2), -2, 1, 2)
   figure, axis = plt.subplots()
   patch = DTStationPatch(station, axis, faceview="phi", vmap="time", data=rows)
   print("vmap:", patch.vmap, "values:", patch.values)
   patch.change_vmap("energy")
   print("vmap:", patch.vmap, "values:", patch.values)
   print("non-zero cells:", int(sum(value != 0 for value in patch.cells_collection.get_array())))

.. code-block:: text

   vmap: time values: {(1, 1, 1): 350.0, (3, 2, 2): 410.0}
   vmap: energy values: {(1, 1, 1): 1.2, (3, 2, 2): 0.7}
   non-zero cells: 2

One row per cell: ``sl``, ``l`` and ``w`` plus any number of value columns. The
identifiers are cast to int, so a float read from ROOT or a CSV still matches.
The column named ``vmap`` colours the cell; a cell without a row, or a row
without that column, is 0. A ``dict``, a list of dicts and a
``pandas.DataFrame`` are all accepted.

``change_vmap`` switches column in place and redraws the same geometry. There is
no per-event state on the station: one station can draw two events, and the
patches never write on it.

What is stable
--------------

- specs and ``validate`` - ``mpldts.geometry.specs``
- the CMS source - ``CMSXMLSource().station(...)`` and ``chamber_keys()``
- model builders - ``build_station``, ``build_detector``
- Station views - ``Station.from_spec``, ``wheel``, ``sector``, ``number``,
  ``name``, ``super_layers``, ``bounds``, ``local_center``, ``global_center``,
  ``transformer``
- patches - ``DTStationPatch``, ``DTRelatedPatch``, ``DTObjectsPatch``,
  ``DTSegmentsPatch``, ``MultiDTSegmentsPatch``, ``AMDTSegments``
- JSON - ``to_json``, ``from_json``, ``to_dict``, ``from_dict``
- export sinks - ``TgSink``, ``export_volumes``, ``iter_volume_placements``,
  ``VolumeSink``

What is internal
----------------

Names starting with ``_`` are not API: ``Station._node``, ``Station._graph``,
``Station._parts``, ``Station._bind``, ``DTStationPatch._drawn_cells``, the
helpers in ``mpldts.geometry.sources.cms_xml``. They exist because the patches
and the source use them; code outside the package must not depend on them.

The pin
-------

dtpr declares the dependency twice in ``pyproject.toml``, as a git URL pinned
to a tag (``...@v2.2.0-beta``) and as a ``rev``. That tag is the API the
package is written against: it changes at releases, not on main. Version 3.0
removed the compatibility layer (``StationsCache``, ``DTGeometry``,
``overlay``, ``dt_info``) and moved per-event values to ``data=``; the
"Version 3.0.0" section of :doc:`../about/changelog` gives the one-line
replacement for each. Read it when you bump the pin, before changing code.
