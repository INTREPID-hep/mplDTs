Describe your own detector
==========================

A spec is data you can write by hand: poses, shapes, cell grids and names.
This page builds a test-beam detector with one station of two super layers and
a lead wall. It is the compact form of ``docs/examples/custom_station.py``.

Build the station
-----------------

``LayerSpec`` is the long dataclass form; ``make_station`` and
``make_superlayer`` only fill in defaults such as the identity pose.

.. code-block:: python

   from mpldts.geometry.constructors import make_station, make_superlayer
   from mpldts.geometry.specs import Box, CellGrid, LayerSpec, Pose

   def layers():
       return [
           LayerSpec(
               number=number,
               pose=Pose.translated(0.0, 0.0, (number - 2.5) * 2.0),
               cells=CellGrid(pitch=4.0, count=8, shape=Box(4.0, 40.0, 1.3), material="GasMixture"),
           )
           for number in range(1, 5)
       ]

   station = make_station(
       "TB-1",
       [
           make_superlayer(1, layers()),
           make_superlayer(2, layers(), pose=Pose.rotated_z(90.0, (0.0, 0.0, 9.5))),
       ],
       shape=Box(42.0, 42.0, 21.3),
   )
   print([super_layer.number for super_layer in station.super_layers], station.shape.dx)

.. code-block:: text

   [1, 2] 42.0

The second super layer is rotated 90 degrees about z and sits 9.5 cm above the
first. Each layer holds eight cells of 4 cm pitch; a cell is
``Box(pitch, length, thickness)``.

The detector and its structural solid
-------------------------------------

.. code-block:: python

   from mpldts.geometry.specs import DetectorSpec, StructureSpec, validate

   detector = DetectorSpec(
       name="testbeam",
       pose=Pose.identity(),
       stations=[station],
       structure=[
           StructureSpec(
               name="lead_wall",
               pose=Pose.translated(0.0, 0.0, -20.0),
               shape=Box(50.0, 50.0, 2.0),
               material="G4_Pb",
           )
       ],
   )
   validate(detector)
   print(detector.name, [entry.name for entry in detector.stations])
   print([part.name for part in detector.structure])

.. code-block:: text

   testbeam ['TB-1']
   ['lead_wall']

``validate`` checks every pose, shape, cell grid and duplicate number.
``StructureSpec`` is passive data, the yoke or a wall in front of the station.
It is not a node and no exporter writes it today.

Build the tree and plot the stations
------------------------------------

.. code-block:: python

   import matplotlib.pyplot as plt
   from mpldts.geometry import Station, build_detector
   from mpldts.patches import DTStationPatch

   node = build_detector(detector)
   print(node.name, [child.name for child in node.children])

   view = Station.from_spec(detector.stations[0])
   figure, axes = plt.subplots(1, 2, figsize=(12, 4))
   for axis, faceview in zip(axes, ("phi", "eta")):
       patch = DTStationPatch(view, axis, faceview=faceview, local=True)
       print(faceview, len(patch.cells_collection.get_paths()))
       axis.set_title("%s %s" % (view.name, faceview))
   figure.savefig("testbeam.png")

.. code-block:: text

   testbeam ['TB-1']
   phi 32
   eta 32

Export the .tg
--------------

.. code-block:: python

   from io import StringIO

   from mpldts.export import TgSink, export_volumes, iter_volume_placements

   print(len(list(iter_volume_placements(node))), "placements")
   text = StringIO()
   export_volumes(node, TgSink(text))
   lines = text.getvalue().splitlines()
   print("\n".join(lines[:6]))
   print(next(line for line in lines if line.startswith(":VOLU DriftCell")))

.. code-block:: text

   65 placements
   // mplDTs .tg export: testbeam

   :SOLID Solid_TB-1 BOX 21.000000*cm 21.000000*cm 10.650000*cm
   :VOLU TB-1 Solid_TB-1 G4_AIR

   :PLACE TB-1 1 world R0 0.000000*cm 0.000000*cm 0.000000*cm
   :VOLU DriftCell_TB-1_SL1 Solid_DriftCell_TB-1_SL1 GasMixture

The 65 placements are the station and its 64 cells; super layers and layers
have no solid and are folded into the cell placements. The lead wall is not in
the file. If it has to be a volume today, model it as a passive ``StationSpec``
(a shape, no super layers) and put it in ``stations``.

See :doc:`geant4` for the record format and the consumer.
