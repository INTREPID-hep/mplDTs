Station
=======

.. autoclass:: mpldts.geometry.station.Station
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__
    :inherited-members:

.. rubric:: Example

A station view is built from a spec and carries the chamber numbers the plotter
labels its window with:

.. code-block:: python

    from mpldts.geometry import Station
    from mpldts.geometry.sources import CMSXMLSource

    source = CMSXMLSource()              # the XML is parsed once
    station = Station.from_spec(source.station(-2, 1, 2), -2, 1, 2)

    print(station.name, [sl.number for sl in station.super_layers])
    print(len(station.super_layer(1).layer(1).cells), "cells in SL1/L1")
    print(tuple(round(float(value), 2) for value in station.global_center))

.. rubric:: Output

.. code-block:: text

    W-2_S1_MB2 [1, 3, 2]
    59 cells in SL1/L1
    (512.48, -21.43, -533.35)

The station holds no per-event data: a value a patch colours comes from the
:``(sl, l, w)`` table passed to the patch (ADR-024).
