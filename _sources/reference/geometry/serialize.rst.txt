Serialize
=========

One local schema for a station or a detector: poses, shapes and names only, no
derived values. Unknown keys, a wrong schema string, a missing field and a bad
type are errors, so a document that loads is a document that validates.

.. autofunction:: mpldts.geometry.serialize.to_dict
    :no-index:

.. autofunction:: mpldts.geometry.serialize.from_dict
    :no-index:

.. autofunction:: mpldts.geometry.serialize.to_json
    :no-index:

.. autofunction:: mpldts.geometry.serialize.from_json
    :no-index:

.. rubric:: Example

.. code-block:: python

    from mpldts.geometry.constructors import make_layer, make_station, make_superlayer
    from mpldts.geometry.serialize import from_json, to_dict, to_json
    from mpldts.geometry.specs import Box, CellGrid

    grid = CellGrid(pitch=4.2, count=24, shape=Box(4.2, 120.0, 1.3), material="GasMixture")
    station = make_station("TB-1", [make_superlayer(1, [make_layer(1, grid)])], shape=Box(110.0, 130.0, 40.0))

    document = to_dict(station)
    print(document["schema"], sorted(document))
    print(sorted(document["super_layers"][0]["layers"][0]["cells"]))
    print(len(to_json(station).splitlines()), "lines of JSON")
    print(from_json(to_json(station)).name, from_json(to_json(station)).material)

.. rubric:: Output

.. code-block:: text

    mpldts.station/2 ['material', 'name', 'pose', 'schema', 'shape', 'super_layers']
    ['count', 'first_id', 'material', 'offset', 'pitch', 'shape']
    106 lines of JSON
    TB-1 G4_AIR

A DetectorSpec uses the ``mpldts.detector/2`` schema and is the document to keep
in a repository; ``from_json`` validates on load. The write path is the same
shape as the read path, field for field, so a round trip is lossless.
