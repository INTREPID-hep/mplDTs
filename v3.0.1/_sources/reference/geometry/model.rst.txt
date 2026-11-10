Model
=====

``build_station`` turns a spec into the runtime node tree. Every node stores
one pose relative to its parent (``p_parent = R * p_child + t``); the builder
composes and caches ``world_pose`` once, top-down. A node with ``shape=None``
is a grouping frame: it matters for transforms and plotting, not for export.

.. code-block:: text

    station
    └── attachment       Box panel bolted to the station
    └── super layer      grouping frame, shape=None
        └── layer        grouping frame, shape=None
            └── cell     Box or Tube, from the layer CellGrid

.. autoclass:: mpldts.geometry.model.Node
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__

.. autofunction:: mpldts.geometry.model.build_station
    :no-index:

.. autofunction:: mpldts.geometry.model.build_detector
    :no-index:

.. rubric:: Example

.. code-block:: python

    from mpldts.geometry.model import build_station
    from mpldts.geometry.sources import CMSXMLSource

    node = build_station(CMSXMLSource().station(-2, 1, 2))

    print(node.kind, node.name, node.frame_id)
    print([(child.name, child.kind, len(child.children)) for child in node.children])
    cell = node.children[0].children[0].children[0]
    print(cell.frame_id)
    print(tuple(round(float(v), 2) for v in cell.world_pose.translation))

.. rubric:: Output

.. code-block:: text

    station W-2_S1_MB2 /W-2_S1_MB2
    [('SL1', 'superlayer', 4), ('SL3', 'superlayer', 4), ('SL2', 'superlayer', 4)]
    /W-2_S1_MB2/SL1/L1/C1
    (498.77, -140.88, -533.35)
