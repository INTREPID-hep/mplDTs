"""T-010: unit tests for the geometry specs."""

import numpy as np
import pytest

from mpldts.geometry.specs import (
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
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
