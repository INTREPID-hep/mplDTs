Frames and transforms
=====================

A frame is the name a pose is measured in. 3.0 keeps one pose per node and
derives the rest; this page is how the names, the graph and the transform call
fit together. The comments in each snippet are its real output.

Frame ids are paths
-------------------

Every node contributes one segment to a slash path below the graph root:
``detector`` (the root), ``station``, ``attachment``, ``superlayer``
(``SL<n>``), ``layer`` (``L<n>``) and ``cell`` (``C<id>``). The plotting
frames ``StationNvPhi``, ``StationNvEta`` and ``SL13Center`` are registered
with ``add_virtual`` and add a segment too, without being nodes.

A station tree from ``build_station`` has no parent, so its root frame id is
``/<station name>``. ``build_detector`` makes the detector the root and
prefixes each station segment with its name: ``/<detector>/<station>``.

.. code-block:: python

   from mpldts.geometry import Station, build_detector
   from mpldts.geometry.constructors import make_detector, make_layer, make_station, make_superlayer
   from mpldts.geometry.sources import CMSXMLSource
   from mpldts.geometry.specs import Box, CellGrid, Pose

   source = CMSXMLSource()
   spec = source.station(-2, 1, 2)
   station = Station.from_spec(spec, -2, 1, 2)
   cell = station.super_layer(1).layer(1).cell(1)

   cells = CellGrid(pitch=4.2, count=2, shape=Box(4.2, 20.0, 1.3))
   layers = [make_layer(1, cells)]
   assembly = build_detector(make_detector("Assembly", [
       make_station("A", [make_superlayer(1, layers)], pose=Pose.translated(100.0, 0.0, 0.0)),
       make_station("B", [make_superlayer(1, layers)], pose=Pose.translated(0.0, 0.0, 50.0)),
   ]))

   # /W-2_S1_MB2, then /W-2_S1_MB2/SL1/L1/C1
   print(station.transformer.node.frame_id)
   print(cell.transformer.node.frame_id)
   # ['/W-2_S1_MB2/Honeycomb']
   print([node.frame_id for node in station.transformer.node.attachments])
   # /Assembly, then /Assembly/A
   print(assembly.frame_id, assembly.children[0].frame_id, sep="\n")

FrameGraph
----------

``FrameGraph`` holds one edge per parent/child pose. ``add_nodes(root)`` walks
the tree, attachments included, and registers each node's pose in its parent;
edges are stored both ways and a ``(from, to)`` cache is cleared on every
change. ``frames()`` is the set of every path, ``has(frame)`` answers
membership, and the lookup is ``matrix(from, to)``, breadth-first: a ``Pose``
or ``None``. ``get_transformation`` wraps it as a 4x4 and warns on a miss;
``transform`` raises ``ValueError``.

.. code-block:: python

   from mpldts.geometry import FrameGraph

   graph = FrameGraph()
   graph.add_nodes(assembly)
   # World 12 True
   print(graph.root, len(graph.frames()), graph.has("/Assembly/A/SL1/L1/C1"))
   # True None
   print(graph.matrix("/Assembly/A/SL1/L1/C1", "World") is not None,
         graph.matrix("/Nope", "World"))
   # [100.   0. -50.]
   print(graph.get_transformation("/Assembly/A", "/Assembly/B")[0:3, 3].round(2))

FrameView and the transform call
--------------------------------

A ``FrameView`` binds the graph to one node: ``station.transformer`` is the
view at the station, ``super_layer.transformer`` and ``cell.transformer`` the
same graph at their node. A name is a full frame id first, then an alias in
scope: ``CMS``/``World`` is the root, ``Station``/``Layer``/``Cell`` the
nearest ancestor of that kind, ``SLn`` the nearest super layer, and another
basename a child of an ancestor (how ``Honeycomb`` and the virtual frames
resolve). ``transform(points, from_frame, to_frame, type="point")`` composes
both paths; ``type="vector"`` uses the rotation only.

``available_frames`` is the membership set a legacy consumer checks before
transforming: every graph frame id plus every legacy name that resolves in this
view's scope. It is per view: the station view does not list ``Cell``, the
cell view does.

.. code-block:: python

   # (498.77, -140.88, -533.35), then (-119.45, 0.0, 13.7)
   centre = cell.transformer.transform((0.0, 0.0, 0.0), "Cell", "CMS")
   back = station.transformer.transform(centre, "CMS", "Station")
   print(tuple(round(float(value), 2) for value in centre))
   print(tuple(round(float(value), 2) for value in back))
   # (0.0, 0.0, 2.67499)
   print(tuple(round(float(value), 5) for value in
         station.transformer.transform((0.0, 0.0, 0.0), "Honeycomb", "Station")))

   # [100.   0. -50.], then [97.9  0.   0. ]
   point = (0.0, 0.0, 0.0)
   print(graph.transform(point, "/Assembly/A", "/Assembly/B"))
   print(graph.transform(point, "/Assembly/A/SL1/L1/C1", "/Assembly"))

   # ['Station', 'CMS', 'Honeycomb'], then ['Cell', 'Station', 'CMS', 'SL1']
   print([name for name in ("Station", "CMS", "Cell", "Honeycomb")
          if name in station.transformer.available_frames])
   print([name for name in ("Cell", "Station", "CMS", "SL1")
          if name in cell.transformer.available_frames])

Composed world_pose
-------------------

``node.world_pose`` is ``parent.world_pose.compose(node.pose)``, composed once
top-down at build time; the graph edges are the same parent-relative poses, so
a path to the root and ``world_pose`` agree. The station view derives the patch
values from it: ``local`` applies ``station.world_pose.inverse()`` to a
child's world translation, ``global`` is that translation, ``direction`` is
the station rotation column and ``bounds`` is the extent of shapes and
children. None is stored on a node or a spec: one pose per node is the only
statement, so a changed parent moves the children and the derived values cannot
disagree.

.. code-block:: python

   cell_node = cell.transformer.node
   # (-121.8, 0.0, 0.0) -> (498.775, -140.88, -533.35)
   print(tuple(round(float(value), 3) for value in cell_node.pose.translation),
         tuple(round(float(value), 3) for value in cell_node.world_pose.translation))
   # (-119.45, 0.0, 13.7)
   print(tuple(round(float(value), 2) for value in cell.local_center))

2.x to 3.0
----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 2.x
     - 3.0
   * - ``DTFrame``
     - view base; the geometry is ``Node``.
   * - ``TransformManager``
     - ``FrameGraph`` plus the per-node ``FrameView`` (``station.transformer``).
   * - ``get_transformation(from, to)``
     - same call on either class, ``p_to = M . p_from``; a miss warns and is ``None``.
   * - ``transform(points, from, to, type=)``
     - ``FrameView.transform(...)``; ``FrameGraph.transform(..., kind=)``.
   * - the ``"SuperLayer"`` alias
     - removed: ``SL1``/``SL2``/``SL3``, or ``Layer`` for the nearest layer.
   * - legacy names in ``available_frames``
     - ``Station``, ``CMS``, ``World``, ``SL<n>``, ``Layer``/``Cell`` in scope,
       ``StationNvPhi``, ``StationNvEta``, ``SL13Center``; ``SectorRef`` is gone.

Rules
-----

- A frame is a slash path, resolved in the scope of the view that asks.
- One pose per node, parent-relative; ``world_pose`` is composed, never written.
- The graph reads the tree; adding an edge never mutates a node.
- A missing path: ``get_transformation`` warns and returns ``None``; ``transform``
  raises ``ValueError``.

