"""T-051: the JSON documents of a detector and a station."""

import io
import json

import numpy as np
import pytest

from mpldts.export import TgSink, export_volumes
from mpldts.geometry import build_station
from mpldts.geometry.serialize import (
    SCHEMA_DETECTOR,
    SCHEMA_STATION,
    from_dict,
    from_json,
    to_dict,
    to_json,
)
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.presets import cms
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

CHAMBER = (-2, 1, 2)


def _station(name="TB-1", pose=None):
    grid = CellGrid(pitch=4.2, count=6, shape=Box(4.2, 40.0, 1.3), material="GasMixture", first_id=3, offset=0.7)
    return StationSpec(
        name=name,
        pose=Pose.identity() if pose is None else pose,
        super_layers=[
            SuperLayerSpec(
                number=1,
                pose=Pose.rotated_z(90.0, (0.0, 0.0, 6.0)),
                layers=[
                    LayerSpec(number=1, pose=Pose.translated(0.0, 0.0, 1.95), cells=grid),
                    LayerSpec(number=2, pose=Pose.translated(0.0, 0.0, -1.95), cells=grid),
                ],
            )
        ],
        shape=Box(32.0, 41.0, 12.0),
        material="G4_AIR",
        attachments=[
            AttachmentSpec(
                name="Honeycomb",
                pose=Pose.translated(0.0, 0.0, 0.5),
                shape=Box(31.0, 40.0, 2.0),
            )
        ],
    )


def _detector():
    return DetectorSpec(
        name="TB-2026",
        pose=Pose.rotated_z(15.0, (10.0, -20.0, 30.0)),
        stations=[_station()],
        shape=Box(200.0, 220.0, 150.0),
        structure=[
            StructureSpec(name="Yoke", pose=Pose.identity(), shape=Box(300.0, 300.0, 200.0))
        ],
    )


def test_a_station_document_has_the_schema_and_no_derived_values():
    document = to_dict(_station())

    assert document["schema"] == SCHEMA_STATION
    assert set(document) == {"schema", "name", "pose", "shape", "material", "super_layers", "attachments"}
    layer = document["super_layers"][0]["layers"][0]
    assert set(layer) == {"number", "pose", "cells"}
    assert layer["cells"] == {
        "pitch": 4.2,
        "count": 6,
        "shape": {"kind": "box", "dx": 4.2, "dy": 40.0, "dz": 1.3},
        "first_id": 3,
        "offset": 0.7,
        "material": "GasMixture",
    }
    # the pose is the parent-relative one, the world pose is never stored
    assert document["super_layers"][0]["pose"]["translation"] == [0.0, 0.0, 6.0]


def test_a_custom_detector_round_trips_through_json():
    spec = _detector()
    text = to_json(spec)

    back = from_json(text)

    validate(back)  # a document that loads is a document that validates
    assert to_dict(back) == to_dict(spec)
    assert json.loads(text)["schema"] == SCHEMA_DETECTOR
    assert back.stations[0].attachments[0].name == "Honeycomb"
    assert back.structure[0].name == "Yoke"


def test_a_cms_station_round_trips_field_by_field():
    source = CMSXMLSource()
    spec = cms.with_attachments(source.station(*CHAMBER), source.record(*CHAMBER))

    back = from_dict(json.loads(to_json(spec)))

    assert to_dict(back) == to_dict(spec)
    assert [sl.number for sl in back.super_layers] == [1, 3, 2]
    assert [len(sl.layers) for sl in back.super_layers] == [4, 4, 4]
    assert back.super_layers[2].pose.rotation[0, 1] == pytest.approx(1.0)
    np.testing.assert_allclose(back.attachments[0].shape.dz, 11.80002, atol=1e-4)


def test_a_tube_cell_round_trips():
    grid = CellGrid(pitch=6.0, count=2, shape=Tube(radius=2.2, length=80.0, axis="z", inner_radius=1.1))
    spec = _station()
    spec.super_layers[0].layers[0] = LayerSpec(
        number=1, pose=Pose.identity(), cells=grid
    )

    back = from_json(to_json(spec))

    assert isinstance(back.super_layers[0].layers[0].cells.shape, Tube)
    assert back.super_layers[0].layers[0].cells.shape.axis == "z"
    assert back.super_layers[0].layers[0].cells.shape.inner_radius == 1.1


def test_the_json_path_builds_and_exports_a_tg():
    spec = from_json(to_json(_detector()))
    stream = io.StringIO()

    export_volumes(build_station(spec.stations[0]), TgSink(stream))
    text = stream.getvalue()

    # the Geant4 name is sanitised: a dash is not safe in a .tg name
    assert ":VOLU TB_1 Solid_TB_1 G4_AIR" in text
    assert ":VOLU DriftCell_TB_1_SL1 Solid_DriftCell_TB_1_SL1 GasMixture" in text
    assert ":VOLU Honeycomb_TB_1 Solid_Honeycomb_TB_1 G4_Al" in text


def test_an_unknown_key_is_rejected():
    document = to_dict(_station())
    document["super_layers"][0]["layers"][0]["pitch"] = 4.2

    with pytest.raises(ValueError, match="unknown 'pitch'"):
        from_dict(document)


def test_an_unknown_schema_is_rejected():
    document = to_dict(_station())
    document["schema"] = "mpldts.station/1"

    with pytest.raises(ValueError, match="unknown schema"):
        from_dict(document)


def test_a_missing_field_is_rejected():
    document = to_dict(_station())
    del document["super_layers"][0]["layers"][0]["pose"]

    with pytest.raises(ValueError, match="missing 'pose'"):
        from_dict(document)


def test_a_wrong_type_is_rejected():
    document = to_dict(_station())
    document["super_layers"][0]["layers"][0]["cells"]["count"] = "6"

    with pytest.raises(ValueError, match="expected an integer"):
        from_dict(document)


def test_a_sheared_rotation_is_rejected():
    document = to_dict(_station())
    document["pose"]["rotation"] = [[1.0, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    with pytest.raises(ValueError, match="not orthonormal"):
        from_dict(document)


def test_a_mirrored_rotation_is_rejected():
    document = to_dict(_station())
    document["pose"]["rotation"] = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]]

    with pytest.raises(ValueError, match="proper rotation"):
        from_dict(document)


def test_a_cell_wider_than_the_pitch_is_rejected():
    document = to_dict(_station())
    document["super_layers"][0]["layers"][0]["cells"]["pitch"] = 2.0

    with pytest.raises(ValueError, match="wider than the pitch"):
        from_dict(document)


def test_text_that_is_not_json_is_rejected():
    with pytest.raises(ValueError, match="not JSON"):
        from_json("{not json")


def test_to_dict_rejects_other_specs():
    with pytest.raises(TypeError, match="DetectorSpec or a StationSpec"):
        to_dict(_station().super_layers[0])
