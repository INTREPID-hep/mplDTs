Volume names
============

A volume name is a contract, not a label. The Geant4 simulation reads the
wheel, the sector, the station, the super layer, the layer and the wire out of
the name, so a name that reads better and parses differently is a geometry
that is silently wrong. Only the exporter names a volume: a node carries a
``name`` and a ``frame_id``, never a volume name, and ``TgSink`` is the one place
that decides (:doc:`model`).

The scheme
----------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Node
     - Name in the ``.tg``
   * - station
     - ``_clean(node.name)``; the CMS source calls a chamber
       ``W<wheel>_S<sector>_MB<station>``, e.g. ``W-2_S1_MB2``
   * - solid
     - ``Solid_`` + the volume name, e.g. ``Solid_W-2_S1_MB2``
   * - cell
     - ``DriftCell_<station>_SL<n>``, e.g. ``DriftCell_W-2_S1_MB2_SL1``
   * - honeycomb panel
     - ``<attachment>_<station>``, e.g. ``Honeycomb_W-2_S1_MB2``
   * - super layer, layer
     - no volume: grouping frames, folded into the cell placements
   * - copy number
     - per (mother, volume), restarting at 1; for a cell it is the wire

A chamber exported with the default names starts like this:

.. code-block:: python

   from io import StringIO

   from mpldts.export import TgSink, export_volumes
   from mpldts.geometry import build_station
   from mpldts.geometry.sources import CMSXMLSource

   node = build_station(CMSXMLSource().station(-2, 1, 2))
   text = StringIO()
   export_volumes(node, TgSink(text))
   print("\n".join(text.getvalue().splitlines()[:15]))

.. code-block:: text

   // mplDTs .tg export: W-2_S1_MB2

   :SOLID Solid_W-2_S1_MB2 BOX 133.399994*cm 125.550003*cm 18.100000*cm
   :VOLU W-2_S1_MB2 Solid_W-2_S1_MB2 G4_AIR

   :ROTM RM_W-2_S1_MB2_1 0.000000 0.000000 -1.000000 1.000000 0.000000 0.000000 0.000000 -1.000000 0.000000
   :PLACE W-2_S1_MB2 1 world RM_W-2_S1_MB2_1 512.475000*cm -21.430000*cm -533.350000*cm
   :SOLID Solid_DriftCell_W-2_S1_MB2_SL1 BOX 2.100000*cm 117.400002*cm 0.650000*cm
   :VOLU DriftCell_W-2_S1_MB2_SL1 Solid_DriftCell_W-2_S1_MB2_SL1 GasMixture

   :PLACE DriftCell_W-2_S1_MB2_SL1 1 W-2_S1_MB2 R0 -119.450000*cm 0.000000*cm 13.700000*cm
   :PLACE DriftCell_W-2_S1_MB2_SL1 2 W-2_S1_MB2 R0 -115.250000*cm 0.000000*cm 13.700000*cm
   :PLACE DriftCell_W-2_S1_MB2_SL1 3 W-2_S1_MB2 R0 -111.050000*cm 0.000000*cm 13.700000*cm
   :PLACE DriftCell_W-2_S1_MB2_SL1 4 W-2_S1_MB2 R0 -106.850001*cm 0.000000*cm 13.700000*cm
   :PLACE DriftCell_W-2_S1_MB2_SL1 5 W-2_S1_MB2 R0 -102.650001*cm 0.000000*cm 13.700000*cm

The file is 725 lines and five volumes: the station, one cell volume per super
layer and the panel. All cells of a super layer share one solid and are placed
as copies 1..n; because the layers are folded, the copy number runs over the
super layer, and ``DriftCellSD`` splits it back into (layer, wire) using the
cells-per-layer encoding in the name. Two nodes with the same base name but a
different shape get ``_2``, ``_3``; the same base and shape is written once.

The sanitiser
-------------

``_clean`` runs on every name the sink writes, the world included. It keeps
ASCII letters, digits, the dash and the underscore, turns every other character
into one underscore, and prefixes one when the first character is a digit (a
Geant4 name cannot start with one):

.. code-block:: python

   from mpldts.export.tg import _clean

   print(_clean("W-2 S1/MB2"))
   print(_clean("W-1"))
   print(_clean("2W"))

.. code-block:: text

   W-2_S1_MB2
   W-1
   _2W

The dash is kept on purpose: it is a legal Geant4 character and it carries the
sign of a negative wheel. Nothing is lowercased, trimmed or shortened.

Why the sign is load-bearing
----------------------------

``StationSD::DecodeStationID`` asks the name for ``_W``, ``_Sec`` and ``_St``, and
``DriftCellSD::DecodeCellID`` adds ``_SL`` and reads the last field as the
cells-per-layer encoding:

.. code-block:: cpp

   stationID.wheel = ExtractIntAfterToken(volumeName, "_W");
   stationID.sector = ExtractIntAfterToken(volumeName, "_Sec");
   stationID.station = ExtractIntAfterToken(volumeName, "_St");

``ExtractIntAfterToken`` copies the text up to the next ``_`` and runs
``std::stoi``, which accepts a leading minus, so ``Station_W-2_Sec1_St2`` is
wheel -2. Before 2.9.1 the sanitiser did not keep the dash and emitted
``W_1``: the token is found, the text up to the next ``_`` is empty, ``stoi``
throws, the decoder returns -999, ``isValid()`` rejects the chamber and the
segment is dropped with a log warning. The yoke names the chamber's solid in
its subtraction (``Solid_Station_W<w>_Sec<s>_St<n>``), so the hole it cuts stops
resolving as well. Worse is a sanitiser that deletes the dash and emits
``W1``: that parses as wheel +1, ``isValid()`` accepts it, and every hit of the
negative chamber is booked on the positive one with no error at all.

What is configurable
--------------------

``TgSink(target, world="world", name_of=None)``. The world name is the mother
written in ``:PLACE`` for a node with none; it must match the volume the
including document defines, because the exporter writes neither the world nor
``R0``. ``name_of`` is ``node -> str or None``: a string replaces the base name
(and is sanitised), ``None`` keeps the default. The root name qualifies the
rotation matrices, ``RM_<root>_<n>``, so two stations in one document never
collide. The same chamber with the simulator's hook:

.. code-block:: python

   def name_of(node):
       if node.kind == "station":
           return "Station_W-2_Sec1_St2"
       if node.kind == "cell":
           sl = node.parent.parent
           return "DriftCell_W-2_Sec1_St2_%s_%s" % (
               sl.name, "".join("%02d" % len(layer.children) for layer in sl.children))
       return None

   export_volumes(node, TgSink(text, name_of=name_of))
   print(next(line for line in text.getvalue().splitlines()
               if line.startswith(":VOLU DriftCell")))

.. code-block:: text

   :VOLU DriftCell_W-2_Sec1_St2_SL1_59606059 Solid_DriftCell_W-2_Sec1_St2_SL1_59606059 GasMixture

An attachment whose hook returns ``None`` keeps
``<attachment name>_<station node name>``; the simulation overrides it as well,
so its panel is ``Honeycomb_W<w>_Sec<s>_St<n>``. The scheme itself is not
configurable: the ``Solid_`` and ``DriftCell_`` prefixes, the ``_SL`` suffix,
the copy numbers and the absence of super layer and layer volumes belong to the
writer. A consumer with a different contract writes another ``VolumeSink``.

Do not
------

- **Do not rename a volume to make a plot read better.** The plot reads
  ``frame_id`` (``/W-2_S1_MB2/SL1/L1/C1``), not the volume name.
- **Do not use the volume name as an identifier in Python.** ``frame_id`` is
  the identifier: unique per node, sink-independent and Geant4-independent.
- **Do not change the sanitiser without a golden identity table.** One row per
  (volume name, copy number) giving the ``(wheel, sector, station, sl, layer,
  wire)`` it decodes to, produced by the old decoder and re-checked with the
  new one, both sides changed together. Until then, the dash stays.
- **Do not put the tokens in free text.** ``_W``, ``_Sec``, ``_St`` and ``_SL``
  are searched by name; a custom name that contains one is decoded at the
  wrong field.
