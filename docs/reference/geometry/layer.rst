Layer
=====

.. autoclass:: mpldts.geometry.layer.Layer
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. rubric:: Example

.. code-block:: python

    from mpldts.geometry import Station
    from mpldts.geometry.sources import CMSXMLSource

    source = CMSXMLSource()
    station = Station.from_spec(source.station(-2, 1, 2), -2, 1, 2)
    layer = station.super_layer(1).layer(1)

    print(layer.number, len(layer.cells), "cells")
    print(layer._first_cell_id, layer._last_cell_id)
    print(tuple(round(float(value), 2) for value in layer.local_center))

.. rubric:: Output

.. code-block:: text

    1 59 cells
    1 59
    (2.35, 0.0, 13.7)
