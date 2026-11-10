Sources
=======

``CMSXMLSource`` is the only reader of the shipped ``DTGeometry_v3.xml``: one
indexed parse per process, and a ``StationSpec`` per chamber. Importing
``mpldts.geometry`` reads no XML; constructing the source is what parses.

.. autoclass:: mpldts.geometry.sources.CMSXMLSource
    :show-inheritance:
    :member-order: bysource
    :members:
    :special-members: __init__

.. rubric:: Example

.. code-block:: python

    from mpldts.geometry.sources import CMSXMLSource

    source = CMSXMLSource()
    print(source.number_of_chambers(), "chambers")
    spec = source.station(-2, 1, 2)
    print(spec.name, [sl.number for sl in spec.super_layers])
    print(source.chamber_of(source.record(-2, 1, 2)["id"]))
    detector = source.detector(chamber_keys=[(-2, 1, 2)])
    print(detector.name, len(detector.stations), len(detector.stations[0].super_layers))
    print(len(source.cell_centres(-2, 1, 2)), "cell centres in the XML")

.. rubric:: Output

.. code-block:: text

    250 chambers
    W-2_S1_MB2 [1, 3, 2]
    (-2, 1, 2)
    CMS 1 3
    704 cell centres in the XML

``station()`` emits the derived poses; ``record()`` keeps the values the XML states
verbatim (raw ids, local positions, bounds) and ``cell_centres()`` the global cell
centres, which is what the 250-chamber oracle compares against.
