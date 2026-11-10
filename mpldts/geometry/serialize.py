"""JSON documents for a detector or a station.

One schema, explicit shapes, no derived values: a document holds poses, shapes
and names only, so a rebuild from JSON produces the same tree as the source
does. Derived data (centres, world poses, cell positions) is never stored.

    {
      "schema": "mpldts.detector/2",
      "name": "TB-2026",
      "pose": {"rotation": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "translation": [0, 0, 0]},
      "stations": [{"name": "TB-1", "pose": ..., "super_layers": [...]}]
    }

The rotation is a 3x3 matrix in rows. Unknown keys, a wrong schema string, a
missing field and a bad type are errors: a document that loads is a document
that validates, so a typo never becomes a silently different detector.
"""

from __future__ import annotations

import json

from mpldts.geometry.specs import (
    AttachmentSpec,
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    StructureSpec,
    SuperLayerSpec,
    Tube,
    validate,
)

__all__ = [
    "SCHEMA_DETECTOR",
    "SCHEMA_STATION",
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
]

SCHEMA_DETECTOR = "mpldts.detector/2"
SCHEMA_STATION = "mpldts.station/2"


# -- writing ---------------------------------------------------------------


def _clean_float(value):
    """Plain float, never -0.0: the documents are read and diffed by people."""
    return float(value) + 0.0


def _pose_to_dict(pose):
    return {
        "rotation": [[_clean_float(value) for value in row] for row in pose.rotation],
        "translation": [_clean_float(value) for value in pose.translation],
    }


def _shape_to_dict(shape):
    if isinstance(shape, Box):
        return {"kind": "box", "dx": float(shape.dx), "dy": float(shape.dy), "dz": float(shape.dz)}
    if isinstance(shape, Tube):
        document = {
            "kind": "tube",
            "radius": float(shape.radius),
            "length": float(shape.length),
            "axis": shape.axis,
        }
        if shape.inner_radius:
            document["inner_radius"] = float(shape.inner_radius)
        return document
    raise ValueError("no JSON shape for %r" % (type(shape).__name__,))


def _grid_to_dict(grid):
    document = {
        "pitch": float(grid.pitch),
        "count": int(grid.count),
        "shape": _shape_to_dict(grid.shape),
        "first_id": int(grid.first_id),
        "offset": float(grid.offset),
    }
    if grid.material is not None:
        document["material"] = grid.material
    return document


def _layer_to_dict(layer):
    document = {"number": int(layer.number), "pose": _pose_to_dict(layer.pose)}
    if layer.shape is not None:
        document["shape"] = _shape_to_dict(layer.shape)
    if layer.material is not None:
        document["material"] = layer.material
    document["cells"] = _grid_to_dict(layer.cells)
    return document


def _super_layer_to_dict(super_layer):
    document = {"number": int(super_layer.number), "pose": _pose_to_dict(super_layer.pose)}
    if super_layer.shape is not None:
        document["shape"] = _shape_to_dict(super_layer.shape)
    if super_layer.material is not None:
        document["material"] = super_layer.material
    document["layers"] = [_layer_to_dict(layer) for layer in super_layer.layers]
    return document


def _attachment_to_dict(attachment):
    return {
        "name": attachment.name,
        "pose": _pose_to_dict(attachment.pose),
        "shape": _shape_to_dict(attachment.shape),
        "material": attachment.material,
    }


def _structure_to_dict(part):
    document = {"name": part.name, "pose": _pose_to_dict(part.pose), "material": part.material}
    if part.shape is not None:
        document["shape"] = _shape_to_dict(part.shape)
    return document


def _station_to_dict(station):
    document = {"name": station.name, "pose": _pose_to_dict(station.pose)}
    if station.shape is not None:
        document["shape"] = _shape_to_dict(station.shape)
    if station.material is not None:
        document["material"] = station.material
    document["super_layers"] = [_super_layer_to_dict(sl) for sl in station.super_layers]
    if station.attachments:
        document["attachments"] = [_attachment_to_dict(a) for a in station.attachments]
    return document


def to_dict(spec):
    """A JSON-ready document for a StationSpec or a DetectorSpec."""
    if isinstance(spec, DetectorSpec):
        document = {"schema": SCHEMA_DETECTOR, "name": spec.name, "pose": _pose_to_dict(spec.pose)}
        if spec.shape is not None:
            document["shape"] = _shape_to_dict(spec.shape)
        document["material"] = spec.material
        document["stations"] = [_station_to_dict(station) for station in spec.stations]
        if spec.structure:
            document["structure"] = [_structure_to_dict(part) for part in spec.structure]
        return document
    if isinstance(spec, StationSpec):
        document = {"schema": SCHEMA_STATION}
        document.update(_station_to_dict(spec))
        return document
    raise TypeError("to_dict() got %r, expected a DetectorSpec or a StationSpec" % (type(spec).__name__,))


def to_json(spec, indent=2):
    """The document as a JSON string."""
    return json.dumps(to_dict(spec), indent=indent) + "\n"


# -- reading ---------------------------------------------------------------

_OPTIONAL = object()


def _mapping(document, where, required, optional=()):
    if not isinstance(document, dict):
        raise ValueError("%s: expected an object, got %r" % (where, type(document).__name__))
    missing = [key for key in required if key not in document]
    if missing:
        raise ValueError("%s: missing %s" % (where, ", ".join(repr(key) for key in missing)))
    unknown = sorted(set(document) - set(required) - set(optional))
    if unknown:
        raise ValueError("%s: unknown %s" % (where, ", ".join(repr(key) for key in unknown)))
    return document


def _number(value, where, default=_OPTIONAL):
    if value is _OPTIONAL:
        if default is _OPTIONAL:
            raise ValueError("%s: missing" % where)
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s: expected a number, got %r" % (where, type(value).__name__))
    return float(value)


def _integer(value, where, default=_OPTIONAL):
    if value is _OPTIONAL:
        if default is _OPTIONAL:
            raise ValueError("%s: missing" % where)
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s: expected an integer, got %r" % (where, type(value).__name__))
    return value


def _text(value, where, default=_OPTIONAL):
    if value is _OPTIONAL:
        if default is _OPTIONAL:
            raise ValueError("%s: missing" % where)
        return default
    if not isinstance(value, str) or not value:
        raise ValueError("%s: expected a non-empty string" % where)
    return value


def _pose_from(value, where):
    document = _mapping(value, where, ("rotation", "translation"))
    return Pose(document["rotation"], document["translation"])


def _shape_from(value, where):
    document = _mapping(
        value,
        where,
        ("kind",),
        ("dx", "dy", "dz", "radius", "length", "axis", "inner_radius"),
    )
    kind = document["kind"]
    fields = {
        "box": ("dx", "dy", "dz"),
        "tube": ("radius", "length", "axis", "inner_radius"),
    }
    extra = sorted(set(document) - {"kind"} - set(fields.get(kind, ())))
    if extra:
        raise ValueError(
            "%s: %s does not take %s" % (where, kind, ", ".join(repr(key) for key in extra))
        )
    if kind == "box":
        return Box(
            _number(document.get("dx", _OPTIONAL), where + " dx"),
            _number(document.get("dy", _OPTIONAL), where + " dy"),
            _number(document.get("dz", _OPTIONAL), where + " dz"),
        )
    if kind == "tube":
        return Tube(
            _number(document.get("radius", _OPTIONAL), where + " radius"),
            _number(document.get("length", _OPTIONAL), where + " length"),
            _text(document.get("axis", _OPTIONAL), where + " axis", "y"),
            _number(document.get("inner_radius", _OPTIONAL), where + " inner_radius", 0.0),
        )
    raise ValueError("%s: unknown shape kind %r" % (where, kind))


def _grid_from(value, where):
    document = _mapping(
        value,
        where,
        ("pitch", "count", "shape"),
        ("first_id", "offset", "material"),
    )
    return CellGrid(
        pitch=_number(document["pitch"], where + " pitch"),
        count=_integer(document["count"], where + " count"),
        shape=_shape_from(document["shape"], where + " shape"),
        first_id=_integer(document.get("first_id", _OPTIONAL), where + " first_id", 1),
        offset=_number(document.get("offset", _OPTIONAL), where + " offset", 0.0),
        material=_text(document.get("material", _OPTIONAL), where + " material", None),
    )


def _layer_from(value, where):
    document = _mapping(value, where, ("number", "pose", "cells"), ("shape", "material"))
    return LayerSpec(
        number=_integer(document["number"], where + " number"),
        pose=_pose_from(document["pose"], where + " pose"),
        cells=_grid_from(document["cells"], where + " cells"),
        shape=_shape_from(document["shape"], where + " shape") if "shape" in document else None,
        material=_text(document.get("material", _OPTIONAL), where + " material", None),
    )


def _super_layer_from(value, where):
    document = _mapping(value, where, ("number", "pose", "layers"), ("shape", "material"))
    if not isinstance(document["layers"], list):
        raise ValueError("%s: layers must be a list" % where)
    return SuperLayerSpec(
        number=_integer(document["number"], where + " number"),
        pose=_pose_from(document["pose"], where + " pose"),
        layers=[
            _layer_from(entry, "%s / layer %d" % (where, index + 1))
            for index, entry in enumerate(document["layers"])
        ],
        shape=_shape_from(document["shape"], where + " shape") if "shape" in document else None,
        material=_text(document.get("material", _OPTIONAL), where + " material", None),
    )


def _attachment_from(value, where):
    document = _mapping(value, where, ("name", "pose", "shape"), ("material",))
    return AttachmentSpec(
        name=_text(document["name"], where + " name"),
        pose=_pose_from(document["pose"], where + " pose"),
        shape=_shape_from(document["shape"], where + " shape"),
        material=_text(document.get("material", _OPTIONAL), where + " material", "G4_Al"),
    )


def _structure_from(value, where):
    document = _mapping(value, where, ("name", "pose"), ("shape", "material"))
    return StructureSpec(
        name=_text(document["name"], where + " name"),
        pose=_pose_from(document["pose"], where + " pose"),
        shape=_shape_from(document["shape"], where + " shape") if "shape" in document else None,
        material=_text(document.get("material", _OPTIONAL), where + " material", "G4_Fe"),
    )


def _station_from(value, where):
    document = _mapping(
        value,
        where,
        ("name", "pose", "super_layers"),
        ("shape", "material", "attachments"),
    )
    super_layers = document["super_layers"]
    if not isinstance(super_layers, list):
        raise ValueError("%s: super_layers must be a list" % where)
    attachments = document.get("attachments", [])
    if not isinstance(attachments, list):
        raise ValueError("%s: attachments must be a list" % where)
    return StationSpec(
        name=_text(document["name"], where + " name"),
        pose=_pose_from(document["pose"], where + " pose"),
        super_layers=[
            _super_layer_from(entry, "%s / super layer %d" % (where, index + 1))
            for index, entry in enumerate(super_layers)
        ],
        shape=_shape_from(document["shape"], where + " shape") if "shape" in document else None,
        material=_text(document.get("material", _OPTIONAL), where + " material", "G4_AIR"),
        attachments=[
            _attachment_from(entry, "%s / attachment %d" % (where, index + 1))
            for index, entry in enumerate(attachments)
        ],
    )


def from_dict(document):
    """Build and validate a StationSpec or a DetectorSpec from a document."""
    if not isinstance(document, dict):
        raise ValueError("document: expected an object, got %r" % (type(document).__name__,))
    if "schema" not in document:
        raise ValueError("document: missing 'schema'")
    schema = document["schema"]
    if schema == SCHEMA_DETECTOR:
        _mapping(document, "detector", ("schema", "name", "pose", "stations"), ("shape", "material", "structure"))
        if not isinstance(document["stations"], list):
            raise ValueError("detector: stations must be a list")
        structure = document.get("structure", [])
        if not isinstance(structure, list):
            raise ValueError("detector: structure must be a list")
        spec = DetectorSpec(
            name=_text(document["name"], "detector name"),
            pose=_pose_from(document["pose"], "detector pose"),
            stations=[
                _station_from(entry, "detector / station %d" % (index + 1))
                for index, entry in enumerate(document["stations"])
            ],
            shape=_shape_from(document["shape"], "detector shape") if "shape" in document else None,
            material=_text(document.get("material", _OPTIONAL), "detector material", "G4_Galactic"),
            structure=[
                _structure_from(entry, "detector / structure %d" % (index + 1))
                for index, entry in enumerate(structure)
            ],
        )
    elif schema == SCHEMA_STATION:
        document = dict(document)
        document.pop("schema")
        spec = _station_from(document, "station")
    else:
        raise ValueError(
            "document: unknown schema %r, expected %r or %r" % (schema, SCHEMA_DETECTOR, SCHEMA_STATION)
        )
    validate(spec)
    return spec


def from_json(text):
    """Build and validate a spec from a JSON string."""
    try:
        document = json.loads(text)
    except ValueError as error:
        raise ValueError("not JSON: %s" % error) from None
    return from_dict(document)
