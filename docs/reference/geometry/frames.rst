Frames
======

``FrameGraph`` holds one edge per parent/child pose and answers queries with a
cache per ``(from, to)`` pair; ``FrameView`` binds the graph to one node and
resolves the legacy names (Station, SL2, Cell, CMS, World) inside that node's
scope. ``graph.matrix(from, to)`` maps from-frame coordinates to to-frame,
the same convention as ``transform``.

.. autoclass:: mpldts.geometry.frames.FrameGraph
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__

.. autoclass:: mpldts.geometry.frames.FrameView
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__

.. rubric:: Example

.. code-block:: python

    from mpldts.geometry.frames import FrameGraph, FrameView
    from mpldts.geometry.model import build_station
    from mpldts.geometry.sources import CMSXMLSource

    node = build_station(CMSXMLSource().station(-2, 1, 2))
    graph = FrameGraph()
    graph.add_nodes(node)
    view = FrameView(graph, node)

    print(view)
    print([name for name in ("Station", "SL2", "Cell") if name in view.available_frames])

    cell = node.children[0].children[0].children[0]
    print(tuple(round(float(v), 2) for v in graph.transform((0.0, 0.0, 0.0), cell.frame_id, "World")))
    print(tuple(round(float(v), 2) for v in FrameView(graph, cell).transform((0.0, 0.0, 0.0), "Cell", "Station")))

.. rubric:: Output

.. code-block:: text

    FrameView: Station <-> CMS <-> World <-> SL1 <-> SL2 <-> SL3 (728 frames)
    ['Station', 'SL2']
    (498.77, -140.88, -533.35)
    (-119.45, 0.0, 13.7)

``Cell`` is an alias of the node the view is bound to, so a view bound to the
station resolves ``Station``, ``SL1``..``SL3`` and the cache names, and a view
bound to a cell also resolves ``Cell``. A query with no path returns None from
``get_transformation`` (with a warning) and raises ValueError from ``transform``.
