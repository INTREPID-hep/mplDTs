Station
=======

.. autoclass:: mpldts.geometry.station.Station
    :members:
    :special-members:
    :private-members: _correct_cords
    :exclude-members: __module__, __dict__, __weakref__

.. rubric:: Example

.. code-block:: python

    local = False
    st = Station(wheel=-2, sector=1, station=4)
    print("Local: ", local)
    print("Station center:", st.local_center if local else st.global_center)
    print("Station direction:", st.direction)
    for sl in st.super_layers:
        print(
            f">Super Layer {sl.number} center:",
            sl.local_center if local else sl.global_center,
        )
        for l in sl.layers:
            print(
                f"->Layer {l.number} center:",
                l.local_center if local else l.global_center,
            )
            print(
                f"---First Cell center:",
                l.cells[0].local_center if local else l.cells[0].global_center,
            )
            print(
                f"---Last Cell center:",
                l.cells[-1].local_center if local else l.cells[-1].global_center,
            )

.. rubric:: Output

.. code-block:: text

    Local:  False
    Station center: (720.2, -94.895, -533.35)
    Station direction: (-1.0, 0.0, 0.0)
    >Super Layer 1 center: (710.25, -90.695, -533.35)
    ->Layer 1 center: (708.3, -91.745, -533.35)
    ---First Cell center: (905.699994, -91.745, -533.35)
    ---Last Cell center: (510.90001186, -91.745, -533.35)
    ->Layer 2 center: (709.6, -91.745, -533.35)
    ---First Cell center: (909.0999850000001, -91.745, -533.35)
    ---Last Cell center: (510.1000030500001, -91.745, -533.35)
    ->Layer 3 center: (710.9, -89.645, -533.35)
    ---First Cell center: (910.399985, -89.645, -533.35)
    ---Last Cell center: (511.40000305000007, -89.645, -533.35)
    ->Layer 4 center: (712.2, -89.645, -533.35)
    ---First Cell center: (909.599994, -89.645, -533.35)
    ---Last Cell center: (514.80001186, -89.645, -533.35)
    >Super Layer 3 center: (733.75, -99.095, -533.35)
    ->Layer 1 center: (731.8, -100.145, -533.35)
    ---First Cell center: (929.199994, -100.145, -533.35)
    ---Last Cell center: (534.40001186, -100.145, -533.35)
    ->Layer 2 center: (733.1, -100.145, -533.35)
    ---First Cell center: (932.5999850000001, -100.145, -533.35)
    ---Last Cell center: (533.6000030500002, -100.145, -533.35)
    ->Layer 3 center: (734.4, -98.045, -533.35)
    ---First Cell center: (933.899985, -98.045, -533.35)
    ---Last Cell center: (534.9000030500001, -98.045, -533.35)
    ->Layer 4 center: (735.7, -98.045, -533.35)
    ---First Cell center: (933.099994, -98.045, -533.35)
    ---Last Cell center: (538.30001186, -98.045, -533.35)
