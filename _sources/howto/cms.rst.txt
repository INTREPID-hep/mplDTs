Work with a CMS chamber
=======================

The CMS source reads ``DTGeometry_v3.xml`` once and emits one ``StationSpec``
per chamber. The spec is frozen data; the plotting view is built from it.

List the chambers
-----------------

.. code-block:: python

   from mpldts.geometry.sources import CMSXMLSource

   source = CMSXMLSource()
   keys = source.chamber_keys()
   print(len(keys), keys[:4])
   print(sorted({key[0] for key in keys}))

.. code-block:: text

   250 [(-2, 1, 1), (-2, 1, 2), (-2, 1, 3), (-2, 1, 4)]
   [-2, -1, 0, 1, 2]

A key is ``(wheel, sector, station)``; ``source.number_of_chambers()`` and
``source.chamber_of(raw_id)`` are the other two lookups.

Get a spec and validate it
--------------------------

.. code-block:: python

   from mpldts.geometry.specs import validate

   spec = source.station(-2, 1, 2)
   validate(spec)
   print(spec.name, tuple(round(float(v), 2) for v in spec.pose.translation))
   print([sl.number for sl in spec.super_layers])
   print([a.name for a in spec.attachments])

.. code-block:: text

   W-2_S1_MB2 (512.48, -21.43, -533.35)
   [1, 3, 2]
   ['Honeycomb']

The XML order is SL1, SL3, SL2. The honeycomb panel is derived from the gap
between the upper and lower super layers, not read from the XML.

Build the view
--------------

.. code-block:: python

   from mpldts.geometry import Station

   station = Station.from_spec(spec, -2, 1, 2)
   print(station.id, station.wheel, station.sector, station.number)
   print(tuple(round(float(value), 2) for value in station.bounds))

.. code-block:: text

   W-2_S1_MB2 -2 1 2
   (266.8, 36.2, 251.1)

``from_spec`` is the only way to build a station. The wheel, sector and
station arguments are labels for the plot; any ``StationSpec`` builds the
same way.

Plot both faces
---------------

.. code-block:: python

   import matplotlib.pyplot as plt
   from mpldts.patches import DTStationPatch

   figure, axes = plt.subplots(1, 2, figsize=(13, 4))
   for axis, faceview in zip(axes, ("phi", "eta")):
       patch = DTStationPatch(station, axis, faceview=faceview, local=True)
       print(faceview, len(patch.cells_collection.get_paths()))
       axis.set_title("%s %s" % (station.id, faceview))
   figure.savefig("chamber_faces.png")

.. code-block:: text

   phi 476
   eta 228

The phi view draws the unturned super layers (SL1, SL3) and eta draws the
turned one (SL2), so each view shows a different set of cells.

Save and load the spec as JSON
------------------------------

.. code-block:: python

   from mpldts.geometry.serialize import from_json, to_json

   text = to_json(spec)
   open("chamber.json", "w").write(text)
   restored = from_json(open("chamber.json").read())
   print(restored.name, len(text), "bytes")

.. code-block:: text

   W-2_S1_MB2 13070 bytes

The document holds poses, shapes and names and never a derived centre.
``from_json`` validates, so a typo is an error rather than a different chamber.

Transform a cell centre to CMS
------------------------------

.. code-block:: python

   cell = station.super_layer(1).layer(1).cell(1)
   centre = (0.0, 0.0, 0.0)
   print([round(float(v), 3) for v in cell.transformer.transform(centre, "Cell", "Station")])
   print([round(float(v), 3) for v in cell.transformer.transform(centre, "Cell", "CMS")])
   print([round(float(v), 3) for v in cell.global_center])

.. code-block:: text

   [-119.45, 0.0, 13.7]
   [498.775, -140.88, -533.35]
   [498.775, -140.88, -533.35]

The third line is the cell centre read back from the node tree. It matches the
second, so the frame graph and the geometry agree.
