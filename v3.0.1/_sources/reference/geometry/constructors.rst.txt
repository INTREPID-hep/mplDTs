Constructors
============

Short builders for hand-written specs: they fill the defaults (identity pose, no
envelope, air in the chamber, vacuum in the world) and leave the rest to the
dataclass. Nothing validates eagerly; ``validate()`` stays the single gate, so a
spec built with these helpers fails exactly where a hand-built one does.

.. autofunction:: mpldts.geometry.constructors.make_layer
    :no-index:

.. autofunction:: mpldts.geometry.constructors.make_superlayer
    :no-index:

.. autofunction:: mpldts.geometry.constructors.make_station
    :no-index:

.. autofunction:: mpldts.geometry.constructors.make_detector
    :no-index:

.. rubric:: Example

.. code-block:: python

    from mpldts.geometry.constructors import make_detector, make_layer, make_station, make_superlayer
    from mpldts.geometry.specs import Box, CellGrid, Pose, validate

    grid = CellGrid(pitch=4.2, count=24, shape=Box(4.2, 120.0, 1.3), material="GasMixture")
    layer = make_layer(1, grid, pose=Pose.rotated_z(-90.0))
    station = make_station("TB-1", [make_superlayer(1, [layer])], shape=Box(110.0, 130.0, 40.0))
    detector = make_detector("TB-2026", [station])

    print(detector.name, detector.material, len(detector.stations))
    print(station.name, station.super_layers[0].layers[0].number, grid.count, "cells")
    print(tuple(round(float(v), 1) for v in station.super_layers[0].layers[0].pose.rotation[0]))
    validate(detector)
    print("validated")

.. rubric:: Output

.. code-block:: text

    TB-2026 G4_Galactic 1
    TB-1 1 24 cells
    (0.0, 1.0, 0.0)
    validated

The four builders only fill defaults: ``make_layer(1, grid)`` is a ``LayerSpec``
with ``Pose.identity()`` and no envelope. A cell is a ``Box`` or a ``Tube`` in the
``CellGrid``, so the same builders describe a test beam and a CMS chamber.
