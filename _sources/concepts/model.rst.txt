Specs, nodes and views
======================

A chamber is one description and three things derived from it: a frozen spec, a
node tree, a view over it - and, for Geant4, a set of volumes. A chamber in 2.x
knew its XML; in 3.0.1 the XML stays in the source.

.. code-block:: text

   specs.py       frozen dataclasses, validate()
      |
      |  build_station(spec) / build_detector(spec)
      v
   model.py       Node tree: station -> superlayer -> layer -> cell
      |           one parent-relative pose per node, world_pose composed
      +-- Station.from_spec(spec) -------> views: Station, SuperLayer, Layer, DriftCell
      +-- iter_volume_placements(root) --> TgSink --> .tg

Specs
-----

``mpldts/geometry/specs.py``: frozen dataclasses, units in cm, no derived value
stored. Every pose is in the parent frame, ``p_parent = R . p_child + t``, so a
spec cannot disagree with its own parent. They are ``eq=False`` because ``Pose``
holds numpy arrays; ``validate()`` is the single gate, and ``build_station``,
``build_detector`` and ``from_json`` call it.

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Dataclass
     - Fields, defaults as written in the dataclass
   * - ``Pose``
     - ``rotation`` (3x3), ``translation`` (3); ``compose``, ``inverse``, ``apply``, ``matrix``
   * - ``Box``
     - ``dx, dy, dz`` full lengths; a drift cell is ``(pitch, length, gap)``
   * - ``Tube``
     - ``radius, length, axis="y", inner_radius=0.0``: a cylinder, optionally a shell
   * - ``CellGrid``
     - ``pitch, count, shape, first_id=1, offset=0.0, material=None``; cells along x
   * - ``LayerSpec``
     - ``number, pose, cells, shape=None, material=None``
   * - ``SuperLayerSpec``
     - ``number, pose, layers, shape=None, material=None``
   * - ``StationSpec``
     - ``name, pose, super_layers, shape=None, material="G4_AIR", attachments=[]``
   * - ``DetectorSpec``
     - ``name, pose, stations, shape=None, material="G4_Galactic", structure=[]``
   * - ``AttachmentSpec``
     - ``name, pose, shape, material="G4_Al"``: the honeycomb panel, shape required
   * - ``StructureSpec``
     - ``name, pose, shape=None, material="G4_Fe"``: the yoke, data only

Nodes
-----

``build_station(spec)`` returns a ``Node``: ``name``, ``kind`` (``station``,
``superlayer``, ``layer``, ``cell``, ``attachment``), ``pose`` in the parent,
``world_pose``, ``frame_id``, ``shape``, ``material``, ``parent``, ``children``,
``attachments``. ``build_detector(spec)`` makes the detector the root and hangs
every station under it, so one tree holds a whole assembly.

.. code-block:: python

   from mpldts.geometry import build_station
   from mpldts.geometry.constructors import make_layer, make_station, make_superlayer
   from mpldts.geometry.specs import Box, CellGrid

   cells = CellGrid(pitch=4.2, count=4, shape=Box(4.2, 120.0, 1.3), material="GasMixture")
   spec = make_station("TB-1", [make_superlayer(1, [make_layer(1, cells)])],
                       shape=Box(110.0, 130.0, 40.0))
   root = build_station(spec)
   walk = (root, root.children[0], root.children[0].children[0])
   print([(node.kind, node.name, node.shape is not None) for node in walk])
   print(root.children[0].children[0].children[0].frame_id)

.. code-block:: text

   [('station', 'TB-1', True), ('superlayer', 'SL1', False), ('layer', 'L1', False)]
   /TB-1/SL1/L1/C1

**A grouping node has no shape.** A super layer and a layer are frames: their
``shape`` is ``None``, their bounds are the union of their children, and an
exporter folds their pose into the next placement instead of writing a volume.
Only a cell carries a solid, and the solid comes from the layer's
``CellGrid``, which carries the gas (``CellGrid.material``), the pitch and the
ids.

Views and export
----------------

``Station.from_spec(spec, wheel=None, sector=None, number=None)`` builds the node
tree and the ``FrameGraph``, registers the plotting frames (``StationNvPhi``,
``StationNvEta``, ``SL13Center``) and derives what the patches read from the
nodes. A ``SuperLayer``, ``Layer`` or ``DriftCell`` is a thin record over one
node: no copy of the geometry and no per-event value (:doc:`events`).
``export_volumes(root, sink)`` folds the grouping frames into
``iter_volume_placements`` and hands each solid to a ``VolumeSink``; ``TgSink``
writes the `.tg` Geant4 reads (:doc:`naming`).

Short constructors versus the dataclass form
--------------------------------------------

The constructors only fill the defaults (identity pose, no envelope, air in the
chamber, vacuum in the world). Both forms produce the same document:

.. code-block:: python

   from mpldts.geometry.constructors import make_layer, make_station, make_superlayer
   from mpldts.geometry.serialize import to_json
   from mpldts.geometry.specs import Box, CellGrid, LayerSpec, Pose, StationSpec, SuperLayerSpec

   cells = CellGrid(pitch=4.2, count=4, shape=Box(4.2, 120.0, 1.3), material="GasMixture")
   short = make_station("TB-1", [make_superlayer(1, [make_layer(1, cells)])])
   long = StationSpec("TB-1", Pose.identity(), [
       SuperLayerSpec(1, Pose.identity(), [LayerSpec(1, Pose.identity(), cells)])])
   print(to_json(short) == to_json(long))

.. code-block:: text

   True

What ``validate()`` rejects
-----------------------------

A pose that is not a proper orthonormal rotation, a shape that is not ``Box`` or
``Tube``, non-positive dimensions, a tube ``inner_radius`` outside
``[0, radius)``, a cell wider than the pitch or cells that do not fit the layer,
``count`` below 1 or ``first_id`` below 1, a duplicate super layer, layer,
station, attachment or structure name, an attachment without a shape, and a
station with neither super layers nor a solid. The message carries the path:

.. code-block:: python

   from mpldts.geometry.specs import Box, CellGrid, LayerSpec, Pose, StationSpec, validate

   bad = [
       LayerSpec(1, Pose.identity(), CellGrid(pitch=0.0, count=4, shape=Box(4.2, 120.0, 1.3))),
       LayerSpec(1, Pose.identity(), CellGrid(pitch=4.2, count=4, shape=Box(6.0, 120.0, 1.3))),
       StationSpec("TB-1", Pose(rotation=[[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 1.0]]), []),
       StationSpec("TB-1", Pose.identity(), []),
   ]
   for spec in bad:
       try:
           validate(spec)
       except ValueError as error:
           print(error)

.. code-block:: text

   layer 1: pitch must be positive, got 0.0
   layer 1: cell is wider than the pitch (6 > 4.2)
   station 'TB-1': rotation is not orthonormal (max deviation 3)
   station 'TB-1': no super layers and no solid
