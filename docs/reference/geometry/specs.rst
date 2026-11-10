Specs
=====

Frozen dataclasses: one parent-relative pose per node, primitive shapes, cell
grids. No I/O, no XML, no backend import, and no derived value stored.
:func:`~mpldts.geometry.specs.validate` is the single gate over a spec tree;
:doc:`model` and :doc:`serialize` both call it.

.. autoclass:: mpldts.geometry.specs.Pose
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.Box
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.Tube
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.CellGrid
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.LayerSpec
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.SuperLayerSpec
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.StationSpec
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.DetectorSpec
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.AttachmentSpec
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autoclass:: mpldts.geometry.specs.StructureSpec
    :no-index:
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. autofunction:: mpldts.geometry.specs.validate

.. rubric:: Example

.. code-block:: python

    from mpldts.geometry.specs import Box, CellGrid, LayerSpec, Pose, validate

    grid = CellGrid(pitch=4.2, count=24, shape=Box(4.2, 120.0, 1.3), material="GasMixture")
    layer = LayerSpec(number=1, pose=Pose.identity(), cells=grid)

    print(layer.number, grid.count, "cells,", grid.ids()[0], "..", grid.ids()[-1])
    print(tuple(round(float(x), 2) for x in grid.x_positions()[:3]))
    print(tuple(round(float(v), 2) for v in Pose.translated(1.0, 2.0, 0.0).apply((10.0, 0.0, 0.0))))
    validate(layer)
    try:
        validate(LayerSpec(number=0, pose=Pose.identity(), cells=grid))
    except ValueError as error:
        print("ValueError:", error)

.. rubric:: Output

.. code-block:: text

    1 24 cells, 1 .. 24
    (-48.3, -44.1, -39.9)
    (11.0, 2.0, 0.0)
    ValueError: layer 0: number must be a positive int, got 0
