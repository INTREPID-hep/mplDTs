SuperLayer
==========

.. autoclass:: mpldts.geometry.super_layer.SuperLayer
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
    super_layer = station.super_layer(1)

    print(super_layer.number, len(super_layer.layers), "layers")
    print(tuple(round(float(value), 2) for value in super_layer.local_center))
    print([layer.number for layer in super_layer.layers])

.. rubric:: Output

.. code-block:: text

    1 4 layers
    (3.4, 0.0, 11.75)
    [1, 2, 3, 4]
