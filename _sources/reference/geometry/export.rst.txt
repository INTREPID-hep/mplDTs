Export
======

A backend only walks placed solids: ``export_volumes`` drives any sink from
``iter_volume_placements``, which folds every grouping node (shape=None) into the
next placement and hands each solid its mother and the pose in that mother.
``TgSink`` writes the Geant4 ASCII format that ``G4tgbVolumeMgr`` reads.

.. autoclass:: mpldts.export.TgSink
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__

.. autofunction:: mpldts.export.export_volumes

.. autofunction:: mpldts.export.iter_volume_placements

.. autoclass:: mpldts.export.VolumePlacement
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__

.. rubric:: Example

.. code-block:: python

    from io import StringIO

    from mpldts.export import TgSink, export_volumes, iter_volume_placements
    from mpldts.geometry.constructors import make_layer, make_station, make_superlayer
    from mpldts.geometry.model import build_station
    from mpldts.geometry.specs import Box, CellGrid

    grid = CellGrid(pitch=4.2, count=2, shape=Box(4.2, 120.0, 1.3), material="GasMixture")
    root = build_station(make_station("TB-1", [make_superlayer(1, [make_layer(1, grid)])], shape=Box(12.0, 130.0, 40.0)))

    placements = list(iter_volume_placements(root))
    print([(p.node.name, None if p.mother is None else p.mother.name) for p in placements])

    target = StringIO()
    export_volumes(root, TgSink(target))
    print("\n".join(target.getvalue().splitlines()[:7]))

.. rubric:: Output

.. code-block:: text

    [('TB-1', None), ('C1', 'TB-1'), ('C2', 'TB-1')]
    // mplDTs .tg export: TB-1

    :SOLID Solid_TB-1 BOX 6.000000*cm 65.000000*cm 20.000000*cm
    :VOLU TB-1 Solid_TB-1 G4_AIR

    :PLACE TB-1 1 world R0 0.000000*cm 0.000000*cm 0.000000*cm
    :SOLID Solid_DriftCell_TB-1_SL1 BOX 2.100000*cm 60.000000*cm 0.650000*cm

The world volume is not written: it belongs to the document that includes the
file. A consumer that parses the volume names passes ``name_of`` to ``TgSink``
(``node -> str or None``) to override the base name of a node.
