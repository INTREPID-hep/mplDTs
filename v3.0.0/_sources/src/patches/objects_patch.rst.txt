DTObjectsPatch
==============

`DTObjectsPatch` draws arbitrary points and polylines of a chamber: hits,
tracks, showers, trigger primitives. Every object is given in any frame the
station graph resolves (`Station`, `CMS`, `SL2`, a cell...) and lands on the
grid the cells use, so the local/global and inverted views come from the same
place as in :doc:`DTStationPatch <dt_station_patch>`.

`objects` is an iterable of `(points, style)` pairs: `points` is an `(N, 3)`
array in `frame` and `style` the keyword arguments of one
`matplotlib.lines.Line2D`. One point is a marker (`linestyle="None"`), two or
more are a polyline; a style given to the constructor applies to every object
and each object's own wins.

.. code-block:: python

    from mpldts.geometry import STATION_CACHE
    from mpldts.patches import DTObjectsPatch

    station = STATION_CACHE.get(0, 1, 1)
    hit = (1.0, 2.0, 3.0)                       # Station coordinates

    DTObjectsPatch(
        station,
        ax,
        [(hit, {"marker": "*", "linestyle": "None", "color": "tab:red"})],
        faceview="phi",
        local=True,
        inverted=True,
    )

.. autoclass:: mpldts.patches.objects_patch.DTObjectsPatch
    :show-inheritance:
    :members:
    :special-members: __init__
    :private-members: _draw_objects, _to_face
