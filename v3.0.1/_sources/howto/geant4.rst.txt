Get the geometry into Geant4
============================

``TgSink`` writes the ASCII text geometry that Geant4's
``G4tgbVolumeMgr`` reads. The walk is backend neutral: the station and its
cells become solids, the super layers and layers are grouping frames whose
poses are folded into the placements.

What the file holds
-------------------

.. code-block:: text

   :SOLID <solid> BOX hx hy hz
   :VOLU <volume> <solid> <material>
   :ROTM <name> m00 m01 m02 m10 m11 m12 m20 m21 m22
   :PLACE <volume> <copy> <mother> <rotation> tx ty tz

- ``:SOLID`` is the shape; box extents are half lengths, in cm.
- ``:VOLU`` binds a volume to its solid and material. The material name must
  exist in the document that includes the file; the CMS gas is ``GasMixture``.
- ``:ROTM`` is written only for a non-identity rotation. ``R0`` is the
  identity and is defined by the including document.
- ``:PLACE`` puts a copy of the volume in its mother. Copy numbers restart
  for every mother; the cell copy number is the wire inside its layer.

One file is one or more stations. The world volume and ``R0`` are not
written: a concentrator includes the file after defining both.

Write one chamber
-----------------

The consumer owns the names, so pass a ``name_of`` hook that reproduces the
scheme its C++ decoders read.

.. code-block:: python

   from io import StringIO

   from mpldts.export import TgSink, export_volumes
   from mpldts.geometry import build_station
   from mpldts.geometry.sources import CMSXMLSource

   wheel, sector, station = 0, 1, 2

   def name_of(node):
       if node.kind == "station":
           return "Station_W%d_Sec%d_St%d" % (wheel, sector, station)
       if node.kind == "cell":
           super_layer = node.parent.parent
           encoding = "".join("%02d" % len(layer.children) for layer in super_layer.children)
           return "DriftCell_W%d_Sec%d_St%d_%s_%s" % (
               wheel, sector, station, super_layer.name, encoding
           )
       return None

   text = StringIO()
   node = build_station(CMSXMLSource().station(wheel, sector, station))
   export_volumes(node, TgSink(text, name_of=name_of))
   lines = text.getvalue().splitlines()
   print("\n".join(lines[:8]))
   print("...")
   print(next(line for line in lines if line.startswith(":VOLU DriftCell")))
   print(next(line for line in lines if line.startswith(":PLACE DriftCell")))
   print(len(lines), "lines")

.. code-block:: text

   // mplDTs .tg export: W0_S1_MB2

   :SOLID Solid_Station_W0_Sec1_St2 BOX 133.399994*cm 125.550003*cm 18.100000*cm
   :VOLU Station_W0_Sec1_St2 Solid_Station_W0_Sec1_St2 G4_AIR

   :ROTM RM_W0_S1_MB2_1 0.000000 0.000000 -1.000000 1.000000 0.000000 0.000000 0.000000 -1.000000 0.000000
   :PLACE Station_W0_Sec1_St2 1 world RM_W0_S1_MB2_1 512.475000*cm -21.430000*cm 0.850000*cm
   :SOLID Solid_DriftCell_W0_Sec1_St2_SL1_59606059 BOX 2.100000*cm 117.400002*cm 0.650000*cm
   ...
   :VOLU DriftCell_W0_Sec1_St2_SL1_59606059 Solid_DriftCell_W0_Sec1_St2_SL1_59606059 GasMixture
   :PLACE DriftCell_W0_Sec1_St2_SL1_59606059 1 Station_W0_Sec1_St2 R0 -119.450000*cm 0.000000*cm 13.700000*cm
   725 lines

Who reads it
------------

The Geant4 simulation application (``DTG4Simulator``) loads the file in
``DetectorConstruction::Construct``:

.. code-block:: cpp

   G4tgbVolumeMgr* volMgr = G4tgbVolumeMgr::GetInstance();
   volMgr->AddTextFile(fGeometryFileName);
   volMgr->ReadAndConstructDetector();

It then registers ``StationSD`` on every logical volume whose name contains
``Station``. When a muon crosses a station, ``StationSD::ProcessHits`` reads
the pre-step volume name and ``DecodeStationID`` calls
``ExtractIntAfterToken(volumeName, "_W")``, ``"_Sec"`` and ``"_St"``, so
``Station_W-1_Sec12_St1`` gives wheel -1, sector 12, station 1.

The names are a contract
------------------------

``TgSink`` defaults to the node names (``W-2_S1_MB2``,
``DriftCell_W-2_S1_MB2_SL1``). The simulation overrides them with the hook
above, and its ``DriftCell`` decoder also reads the super layer and the
cells-per-layer encoding, then maps the copy number to the layer and wire.
Renaming a volume breaks that decode without any Python error. Before a rename,
pin the current names in a golden table and change both sides together.

GDML is not written yet
-----------------------

Only ``.tg`` exists. A ``PyG4ometrySink`` behind the same ``VolumeSink``
seam is an idea on the roadmap (:doc:`../about/roadmap`), not code in this
release.
