Events and per-event data
=========================

The geometry is built once; an event is a table. A ``Station`` is the same
object for every event: its spec is frozen, its nodes hold poses and shapes,
and its views read that tree. None of them gains a value when an event
arrives, so two events can never disagree about the chamber.

.. code-block:: python

   import matplotlib.pyplot as plt
   from mpldts.geometry import Station
   from mpldts.geometry.sources import CMSXMLSource
   from mpldts.patches import DTStationPatch

   station = Station.from_spec(CMSXMLSource().station(-2, 1, 2), -2, 1, 2)
   figure, axis = plt.subplots(figsize=(12, 2.6))
   print(station.id, sum(len(layer.cells) for sl in station.super_layers for layer in sl.layers))

.. code-block:: text

   W-2_S1_MB2 704

The rule
--------

A per-event value belongs to the table handed to the patch, not to the
geometry. Do not copy the station per event and do not write on a spec, a node
or a view: that side channel is what used to leak one event into the next.
``DTStationPatch(station, axis, data=rows, vmap="time")`` draws the station
as it is and colours only the cells that have a row.

The table
---------

A row is keyed by ``sl``, ``l`` and ``w`` (super layer, layer, wire) and may
carry any number of value columns. The same rows arrive as a
``pandas.DataFrame``, as one ``dict`` or as a list of dicts. The ids are cast
to ``int`` when the patch reads them: a column read from a ROOT branch is a
``float``, and ``(1.0, 2.0, 60.0)`` would never match a cell.

.. code-block:: python

   from pandas import DataFrame

   row = {"sl": 1.0, "l": 2.0, "w": 60.0, "time": 410}
   for table in (row, [row], DataFrame([row])):
       patch = DTStationPatch(station, axis, faceview="phi", data=table)
       print(patch.values[(1, 2, 60)])

.. code-block:: text

   410
   410
   410

A cell with no row, or with no ``vmap`` column, is drawn at 0. Here one row
lights one cell and the other 475 stay at 0; the cell that has no row reads
as 0.

.. code-block:: python

   rows = [{"sl": 1, "l": 1, "w": 1, "time": 350}]
   patch = DTStationPatch(station, axis, faceview="phi", data=rows)
   print("cells", len(patch.cells_collection.get_paths()),
         "with data", int((patch.cells_collection.get_array() > 0).sum()))
   print("missing", patch.values.get((1, 2, 60), 0))

.. code-block:: text

   cells 476 with data 1
   missing 0

``vmap``
--------

``vmap`` names the column that colours the cells; it defaults to ``"time"``.
Pass another name at construction, or call ``patch.change_vmap("width")`` to
re-colour from the rows the patch already holds. Only the value array is
recomputed; the rectangles are not rebuilt.

.. code-block:: python

   rows = [{"sl": 1, "l": 2, "w": 60, "time": 410, "width": 4.2}]
   patch = DTStationPatch(station, axis, faceview="phi", data=rows)
   print(patch.vmap, patch.values[(1, 2, 60)], len(patch.cells_collection.get_paths()))
   patch.change_vmap("width")
   print(patch.vmap, patch.values[(1, 2, 60)], len(patch.cells_collection.get_paths()))

.. code-block:: text

   time 410 476
   width 4.2 476

Two events on one station
-------------------------

One station, one geometry, two tables. The consumer in
``DTPatternRecognition`` builds a DataFrame from the event particles, checks
``sl``, ``l`` and ``w``, slices the value column it wants, and passes the
result as ``data=`` to one patch per view. The counts below are the drawn
cells, the cells with a row, and the sum of ``time``.

.. code-block:: python

   events = {
       "event 1": [{"sl": 1.0, "l": 1.0, "w": 1.0, "time": 350},
                   {"sl": 1.0, "l": 2.0, "w": 60.0, "time": 410},
                   {"sl": 3.0, "l": 4.0, "w": 2.0, "time": 500}],
       "event 2": [{"sl": 1.0, "l": 3.0, "w": 30.0, "time": 300},
                   {"sl": 3.0, "l": 2.0, "w": 60.0, "time": 450}],
   }
   figure, axes = plt.subplots(1, 2, figsize=(12, 2.6))
   for axis, (name, rows) in zip(axes, events.items()):
       patch = DTStationPatch(station, axis, faceview="phi", vmap="time", data=rows)
       values = patch.cells_collection.get_array()
       print(name, "drawn", len(patch.cells_collection.get_paths()),
             "with data", int((values > 0).sum()), "time", int(values.sum()))

.. code-block:: text

   event 1 drawn 476 with data 3 time 1260
   event 2 drawn 476 with data 2 time 750

The overlay that is gone
------------------------

2.x had a stateful overlay: ``StationsCache.get(..., dt_info=...)`` returned
a per-event overlay of the station, ``station.overlay(dt_info)`` and
``station.set_cell_attrs(...)`` wrote the values on its cells, and the patch
read ``dt_info`` back from them. That is how one event leaked into the next.
The API was removed in 3.0; write this instead:

.. list-table::
   :header-rows: 1
   :widths: 48 52

   * - 2.x
     - 3.0.1
   * - ``StationsCache.get(dt_info=rows)``, ``station.overlay(rows)``, ``cell.attrs``
     - ``DTStationPatch(..., data=rows, vmap="time")``; the geometry is untouched
   * - ``station.set_cell_attrs(rows)``, then read ``cell.attrs`` / ``dt_info``
     - ``patch.values[(sl, l, w)]``; ``patch.change_vmap("other")`` to re-colour

The replacement is the table itself. There is no station copy, no per-event
attribute on a spec, node or view, and no cache to invalidate.

Other patches
-------------

``DTObjectsPatch`` draws points and polylines (hits, tracks, showers) in any
frame the station graph resolves. One point is a marker, two or more are a
polyline; the coordinates are projected exactly like the cells.

.. code-block:: python

   from mpldts.patches import DTObjectsPatch

   start = station.super_layer(1).layer(2).cell(60).local_center
   end = station.super_layer(3).layer(4).cell(2).local_center
   objects = DTObjectsPatch(station, axis, objects=[
       ([start], {"linestyle": "None", "marker": "*", "color": "tab:red"}),
       ([start, end], {"color": "tab:blue"}),
   ])
   print(len(objects.lines), [len(line.get_xdata()) for line in objects.lines])

.. code-block:: text

   2 [1, 2]

``DTSegmentsPatch`` draws the AM trigger segments of one station. A segment
row carries ``sl``, ``angle`` and ``position`` plus value columns such as
``quality``; ``AMDTSegments`` turns the rows into per-event segments. Phi
draws ``sl != 2``, eta draws ``sl == 2``. ``MultiDTSegmentsPatch`` groups
the same rows by ``(wh, sc, st)`` and makes one patch per parent station.

.. code-block:: python

   from mpldts.geometry import AMDTSegments
   from mpldts.patches import DTSegmentsPatch, MultiDTSegmentsPatch

   rows = [{"parent": station, "sl": 1, "angle": 10.0, "position": 0.0, "quality": 7},
           {"parent": station, "sl": 2, "angle": 5.0, "position": 3.0, "quality": 9}]
   segments = AMDTSegments(rows, reference_frame="Station")
   phi = DTSegmentsPatch(segments, axis, faceview="phi")
   eta = DTSegmentsPatch(segments, axis, faceview="eta")
   print(phi.segments_collection.get_array(), eta.segments_collection.get_array())

   other = Station.from_spec(CMSXMLSource().station(-2, 1, 3), -2, 1, 3)
   rows = [{"parent": station, "sl": 1, "angle": 10.0, "position": 0.0, "quality": 7},
           {"parent": other, "sl": 3, "angle": 20.0, "position": 0.0, "quality": 9}]
   multi = MultiDTSegmentsPatch(AMDTSegments(rows, reference_frame="Station"),
                                axis, faceview="phi")
   print(list(multi.patches),
         {key: len(p.segments_collection.get_paths()) for key, p in multi.patches.items()})

.. code-block:: text

   [7] [9]
   [(-2, 1, 2), (-2, 1, 3)] {(-2, 1, 2): 1, (-2, 1, 3): 1}

The contract is the same: the station is built once, the rows are the event,
and nothing is written on the station or its cells.
