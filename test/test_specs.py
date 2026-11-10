"""The spec dataclasses, their validation, the constructors and JSON documents."""

import io
import json

import numpy as np
import pytest

from mpldts.export import TgSink, export_volumes
from mpldts.geometry import build_detector, build_station
from mpldts.geometry.constructors import make_detector, make_layer, make_station, make_superlayer
from mpldts.geometry.serialize import (
    SCHEMA_DETECTOR,
    SCHEMA_STATION,
    from_dict,
    from_json,
    to_dict,
    to_json,
)
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

PITCH = 4.2
CELL = Box(4.2, 234.8, 1.3)


def _cms_layers(counts=(49, 50, 49, 48), first_ids=(1, 1, 1, 2)):
    return [
        LayerSpec(
            number=index + 1,
            pose=Pose.translated(-1.6, 0.0, 13.7 - 1.3 * index),
            cells=CellGrid(PITCH, count, CELL, first_id=first_id),
        )
        for index, (count, first_id) in enumerate(zip(counts, first_ids))
    ]


def _cms_station(name="MB2"):
    return StationSpec(
        name=name,
        pose=Pose.identity(),
        shape=Box(218.0, 36.2, 251.1),
        super_layers=[
            SuperLayerSpec(number=1, pose=Pose.translated(0, 0, 11.75), layers=_cms_layers()),
            SuperLayerSpec(number=2, pose=Pose.rotated_z(90, (0, 0, -8.0)), layers=_cms_layers()),
        ],
    )


def _cms_detector():
    return DetectorSpec(name="CMS", pose=Pose.identity(), stations=[_cms_station()])


# -- Pose ------------------------------------------------------------------


def test_pose_identity_is_a_no_op():
    point = (1.0, 2.0, 3.0)

    np.testing.assert_allclose(Pose.identity().apply(point), point)


def test_pose_compose_matches_the_matrix_product():
    parent = Pose.rotated_z(30.0, (1.0, 2.0, 3.0))
    child = Pose.rotated_z(-15.0, (0.0, 5.0, -2.0))

    np.testing.assert_allclose(
        parent.compose(child).matrix(), parent.matrix() @ child.matrix(), atol=1e-12
    )


def test_pose_inverse_round_trips_within_1e_9():
    pose = Pose.rotated_z(37.0, (10.0, -3.0, 7.0))
    point = np.array([4.0, -5.0, 6.0])

    identity = pose.compose(pose.inverse()).matrix()
    np.testing.assert_allclose(identity, np.eye(4), atol=1e-9)
    np.testing.assert_allclose(pose.inverse().apply(pose.apply(point)), point, atol=1e-9)


def test_pose_rotated_z_turns_x_into_y():
    np.testing.assert_allclose(Pose.rotated_z(90).apply((1.0, 0.0, 0.0)), (0.0, 1.0, 0.0), atol=1e-12)


def test_pose_vector_ignores_the_translation():
    pose = Pose.rotated_z(90.0, (100.0, 0.0, 0.0))

    np.testing.assert_allclose(pose.apply((1.0, 0.0, 0.0), kind="vector"), (0.0, 1.0, 0.0), atol=1e-12)


def test_pose_applies_to_many_points():
    points = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    np.testing.assert_allclose(
        Pose.rotated_z(90).apply(points), [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]], atol=1e-12
    )


def test_pose_rejects_a_wrong_rotation_shape():
    with pytest.raises(ValueError, match="shape"):
        Pose(np.eye(2))


# -- Shapes ----------------------------------------------------------------


def test_box_aabb_and_volume():
    box = Box(4.2, 234.8, 1.3)

    assert box.aabb() == (4.2, 234.8, 1.3)
    assert box.volume() == pytest.approx(4.2 * 234.8 * 1.3)


def test_tube_aabb_volume_and_axis():
    tube = Tube(radius=2.2, length=100.0)

    assert tube.axis == "y"
    assert tube.aabb() == pytest.approx((4.4, 100.0, 4.4))
    assert tube.volume() == pytest.approx(np.pi * 2.2**2 * 100.0)
    assert tube.symmetry_axis() == "y"
    assert Tube(2.2, 100.0, axis="z").aabb() == pytest.approx((4.4, 4.4, 100.0))


def test_tube_shell_volume():
    shell = Tube(radius=2.2, length=10.0, inner_radius=1.0)

    assert shell.volume() == pytest.approx(np.pi * (2.2**2 - 1.0**2) * 10.0)


# -- CellGrid --------------------------------------------------------------


def test_cell_grid_reproduces_the_cms_pattern():
    counts = (49, 50, 49, 48)
    first = (-100.8, -102.9, -100.8, -98.7)

    for count, expected_first in zip(counts, first):
        positions = CellGrid(PITCH, count, CELL).x_positions()
        assert positions.shape == (count,)
        assert positions[0] == pytest.approx(expected_first)
        np.testing.assert_allclose(np.diff(positions), PITCH)


def test_cell_grid_ids_start_at_first_id():
    grid = CellGrid(PITCH, 48, CELL, first_id=2)

    assert grid.ids()[0] == 2
    assert grid.ids()[-1] == 49


def test_cell_grid_offset_shifts_every_cell():
    plain = CellGrid(PITCH, 49, CELL)
    shifted = CellGrid(PITCH, 49, CELL, offset=-PITCH / 2)

    np.testing.assert_allclose(shifted.x_positions(), plain.x_positions() - PITCH / 2)


# -- validate --------------------------------------------------------------


def test_validate_accepts_a_cms_detector():
    validate(_cms_detector())


def test_validate_accepts_a_single_layer():
    validate(_cms_layers()[0])


def test_validate_rejects_a_negative_box():
    layer = LayerSpec(1, Pose.identity(), CellGrid(PITCH, 4, Box(-4.2, 10.0, 1.3)))

    with pytest.raises(ValueError, match="positive"):
        validate(layer)


def test_validate_rejects_a_non_orthonormal_rotation():
    bad = Pose(np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 1.0]]))
    layer = LayerSpec(1, bad, CellGrid(PITCH, 4, CELL))

    with pytest.raises(ValueError, match="orthonormal"):
        validate(layer)


def test_validate_rejects_cells_wider_than_the_pitch():
    layer = LayerSpec(1, Pose.identity(), CellGrid(PITCH, 4, Box(4.3, 10.0, 1.3)))

    with pytest.raises(ValueError, match="wider than the pitch"):
        validate(layer)


def test_validate_rejects_cells_wider_than_the_layer():
    layer = LayerSpec(1, Pose.identity(), CellGrid(PITCH, 49, CELL), shape=Box(100.0, 10.0, 1.3))

    with pytest.raises(ValueError, match="do not fit the layer"):
        validate(layer)


def test_validate_rejects_a_zero_pitch():
    layer = LayerSpec(1, Pose.identity(), CellGrid(0.0, 4, CELL))

    with pytest.raises(ValueError, match="pitch"):
        validate(layer)


def test_validate_rejects_duplicate_super_layer_numbers():
    station = _cms_station()
    duplicated = StationSpec(
        name=station.name,
        pose=station.pose,
        shape=station.shape,
        super_layers=[station.super_layers[0], station.super_layers[0]],
    )

    with pytest.raises(ValueError, match="duplicate super layer"):
        validate(duplicated)


def test_specs_are_frozen():
    layer = _cms_layers()[0]

    with pytest.raises(AttributeError):
        layer.number = 2


# -- passive solids --------------------------------------------------------


def _passive_wall(name="LeadWall", material="G4_Pb", z=0.0):
    return StationSpec(
        name=name,
        pose=Pose.translated(0.0, 0.0, z),
        super_layers=[],
        shape=Box(100.0, 100.0, 5.0),
        material=material,
    )


def test_a_passive_solid_validates():
    validate(_passive_wall())


def test_a_station_with_neither_a_solid_nor_super_layers_is_rejected():
    with pytest.raises(ValueError, match="no super layers and no solid"):
        validate(StationSpec(name="empty", pose=Pose.identity(), super_layers=[]))


# -- detector structure ----------------------------------------------------


def _structure_station(name="MB"):
    return StationSpec(
        name=name,
        pose=Pose.identity(),
        super_layers=[
            SuperLayerSpec(
                number=1,
                pose=Pose.identity(),
                layers=[
                    LayerSpec(
                        number=1,
                        pose=Pose.identity(),
                        cells=CellGrid(pitch=4.0, count=8, shape=Box(4.0, 8.0, 1.3)),
                    )
                ],
            )
        ],
        shape=Box(32.0, 8.0, 8.8),
    )


def _structure_detector(structure=()):
    return DetectorSpec(
        name="detector",
        pose=Pose.identity(),
        stations=[_structure_station()],
        structure=list(structure),
    )


def test_a_structure_entry_can_have_no_shape():
    validate(_structure_detector([StructureSpec("Yoke", Pose.identity())]))


def test_structure_is_validated():
    yoke = StructureSpec("Yoke", Pose.identity())
    with pytest.raises(ValueError, match="duplicate structure name"):
        validate(_structure_detector([yoke, yoke]))
    with pytest.raises(ValueError, match="pose must be a Pose"):
        validate(_structure_detector([StructureSpec("Yoke", None)]))
    with pytest.raises(ValueError, match="needs a non-empty name"):
        validate(_structure_detector([StructureSpec("", Pose.identity())]))


# -- attachments -----------------------------------------------------------


def _attachment_station(attachments=()):
    return StationSpec(
        name="custom",
        pose=Pose.identity(),
        super_layers=[
            SuperLayerSpec(
                number=1,
                pose=Pose.identity(),
                layers=[
                    LayerSpec(
                        number=1,
                        pose=Pose.identity(),
                        cells=CellGrid(pitch=4.0, count=8, shape=Box(4.0, 8.0, 1.3)),
                    )
                ],
                shape=None,
            )
        ],
        shape=Box(32.0, 8.0, 8.8),
        attachments=list(attachments),
    )


def test_attachments_are_validated():
    with pytest.raises(ValueError, match="duplicate attachment name"):
        validate(
            _attachment_station(
                [
                    AttachmentSpec("Panel", Pose.identity(), Box(1.0, 1.0, 1.0)),
                    AttachmentSpec("Panel", Pose.identity(), Box(1.0, 1.0, 1.0)),
                ]
            )
        )
    with pytest.raises(ValueError, match="needs a shape"):
        validate(_attachment_station([AttachmentSpec("Panel", Pose.identity(), None)]))


# -- the short constructors ------------------------------------------------


def _constructor_grid():
    return CellGrid(pitch=4.2, count=24, shape=Box(4.2, 120.0, 1.3), material="GasMixture")


def test_the_builders_fill_the_defaults():
    layer = make_layer(1, _constructor_grid())
    super_layer = make_superlayer(2, [layer])
    station = make_station("TB-1", [super_layer])

    assert layer.pose.rotation == pytest.approx(Pose.identity().rotation)
    assert layer.shape is None and layer.material is None
    assert super_layer.pose.translation == pytest.approx((0.0, 0.0, 0.0))
    assert station.material == "G4_AIR"
    assert station.attachments == []
    assert station.shape is None


def test_a_built_spec_is_the_same_document_as_the_long_hand_written_one():
    layer = make_layer(1, _constructor_grid(), pose=Pose.translated(0.0, 0.0, 1.95))
    super_layer = make_superlayer(1, [layer], pose=Pose.translated(0.0, 0.0, 6.0))
    short = make_detector(
        "TB-2026",
        [make_station("TB-1", [super_layer], shape=Box(110.0, 130.0, 40.0))],
        pose=Pose.rotated_z(15.0, (10.0, 0.0, 0.0)),
    )

    long = DetectorSpec(
        name="TB-2026",
        pose=Pose.rotated_z(15.0, (10.0, 0.0, 0.0)),
        stations=[
            StationSpec(
                name="TB-1",
                pose=Pose.identity(),
                super_layers=[
                    SuperLayerSpec(
                        number=1,
                        pose=Pose.translated(0.0, 0.0, 6.0),
                        layers=[
                            LayerSpec(
                                number=1,
                                pose=Pose.translated(0.0, 0.0, 1.95),
                                cells=_constructor_grid(),
                            )
                        ],
                    )
                ],
                shape=Box(110.0, 130.0, 40.0),
            )
        ],
    )

    validate(short)
    assert to_dict(short) == to_dict(long)
    assert build_detector(short).children[0].name == "TB-1"


# -- JSON documents --------------------------------------------------------


SERIALIZE_CHAMBER = (-2, 1, 2)


def _serialize_station(name="TB-1", pose=None):
    grid = CellGrid(
        pitch=4.2, count=6, shape=Box(4.2, 40.0, 1.3), material="GasMixture", first_id=3, offset=0.7
    )
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


def _serialize_detector():
    return DetectorSpec(
        name="TB-2026",
        pose=Pose.rotated_z(15.0, (10.0, -20.0, 30.0)),
        stations=[_serialize_station()],
        shape=Box(200.0, 220.0, 150.0),
        structure=[
            StructureSpec(name="Yoke", pose=Pose.identity(), shape=Box(300.0, 300.0, 200.0))
        ],
    )


def test_a_station_document_has_the_schema_and_no_derived_values():
    document = to_dict(_serialize_station())

    assert document["schema"] == SCHEMA_STATION
    assert set(document) == {
        "schema", "name", "pose", "shape", "material", "super_layers", "attachments"
    }
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
    spec = _serialize_detector()
    text = to_json(spec)

    back = from_json(text)

    validate(back)  # a document that loads is a document that validates
    assert to_dict(back) == to_dict(spec)
    assert json.loads(text)["schema"] == SCHEMA_DETECTOR
    assert back.stations[0].attachments[0].name == "Honeycomb"
    assert back.structure[0].name == "Yoke"


def test_a_cms_station_round_trips_field_by_field(source):
    spec = source.station(*SERIALIZE_CHAMBER)

    back = from_dict(json.loads(to_json(spec)))

    assert to_dict(back) == to_dict(spec)
    assert [sl.number for sl in back.super_layers] == [1, 3, 2]
    assert [len(sl.layers) for sl in back.super_layers] == [4, 4, 4]
    assert back.super_layers[2].pose.rotation[0, 1] == pytest.approx(1.0)
    np.testing.assert_allclose(back.attachments[0].shape.dz, 11.80002, atol=1e-4)


def test_a_tube_cell_round_trips():
    grid = CellGrid(pitch=6.0, count=2, shape=Tube(radius=2.2, length=80.0, axis="z", inner_radius=1.1))
    spec = _serialize_station()
    spec.super_layers[0].layers[0] = LayerSpec(number=1, pose=Pose.identity(), cells=grid)

    back = from_json(to_json(spec))

    assert isinstance(back.super_layers[0].layers[0].cells.shape, Tube)
    assert back.super_layers[0].layers[0].cells.shape.axis == "z"
    assert back.super_layers[0].layers[0].cells.shape.inner_radius == 1.1


def test_the_json_path_builds_and_exports_a_tg():
    spec = from_json(to_json(_serialize_detector()))
    stream = io.StringIO()

    export_volumes(build_station(spec.stations[0]), TgSink(stream))
    text = stream.getvalue()

    # the name is sanitised but keeps its dash: StationSD reads the wheel as
    # "_W-1", so the sign is part of the contract (2.9.1)
    assert ":VOLU TB-1 Solid_TB-1 G4_AIR" in text
    assert ":VOLU DriftCell_TB-1_SL1 Solid_DriftCell_TB-1_SL1 GasMixture" in text
    assert ":VOLU Honeycomb_TB-1 Solid_Honeycomb_TB-1 G4_Al" in text


def test_an_unknown_key_is_rejected():
    document = to_dict(_serialize_station())
    document["super_layers"][0]["layers"][0]["pitch"] = 4.2

    with pytest.raises(ValueError, match="unknown 'pitch'"):
        from_dict(document)


def test_an_unknown_schema_is_rejected():
    document = to_dict(_serialize_station())
    document["schema"] = "mpldts.station/1"

    with pytest.raises(ValueError, match="unknown schema"):
        from_dict(document)


def test_a_missing_field_is_rejected():
    document = to_dict(_serialize_station())
    del document["super_layers"][0]["layers"][0]["pose"]

    with pytest.raises(ValueError, match="missing 'pose'"):
        from_dict(document)


def test_a_wrong_type_is_rejected():
    document = to_dict(_serialize_station())
    document["super_layers"][0]["layers"][0]["cells"]["count"] = "6"

    with pytest.raises(ValueError, match="expected an integer"):
        from_dict(document)


def test_a_shape_does_not_take_the_fields_of_another_kind():
    document = to_dict(_serialize_station())
    document["super_layers"][0]["layers"][0]["cells"]["shape"]["radius"] = 2.2

    with pytest.raises(ValueError, match="does not take 'radius'"):
        from_dict(document)


def test_a_sheared_rotation_is_rejected():
    document = to_dict(_serialize_station())
    document["pose"]["rotation"] = [[1.0, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    with pytest.raises(ValueError, match="not orthonormal"):
        from_dict(document)


def test_a_mirrored_rotation_is_rejected():
    document = to_dict(_serialize_station())
    document["pose"]["rotation"] = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]]

    with pytest.raises(ValueError, match="proper rotation"):
        from_dict(document)


def test_a_cell_wider_than_the_pitch_is_rejected():
    document = to_dict(_serialize_station())
    document["super_layers"][0]["layers"][0]["cells"]["pitch"] = 2.0

    with pytest.raises(ValueError, match="wider than the pitch"):
        from_dict(document)


def test_text_that_is_not_json_is_rejected():
    with pytest.raises(ValueError, match="not JSON"):
        from_json("{not json")


def test_to_dict_rejects_other_specs():
    with pytest.raises(TypeError, match="DetectorSpec or a StationSpec"):
        to_dict(_serialize_station().super_layers[0])
