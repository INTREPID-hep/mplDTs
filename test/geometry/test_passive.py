"""A station is a chamber, or a passive solid with a pose (3.0.1)."""

import numpy as np
import pytest

from mpldts.geometry import Station, build_detector, build_station
from mpldts.geometry.specs import Box, DetectorSpec, Pose, StationSpec, validate


def _wall(name="LeadWall", material="G4_Pb", z=0.0):
    return StationSpec(
        name=name,
        pose=Pose.translated(0.0, 0.0, z),
        super_layers=[],
        shape=Box(100.0, 100.0, 5.0),
        material=material,
    )


def test_a_station_without_super_layers_but_with_a_solid_is_a_passive_volume():
    spec = _wall()
    validate(spec)

    node = build_station(spec)

    assert node.kind == "station"
    assert node.children == []
    assert node.shape.aabb() == (100.0, 100.0, 5.0)
    assert node.material == "G4_Pb"


def test_a_station_with_neither_a_solid_nor_super_layers_is_rejected():
    with pytest.raises(ValueError, match="no super layers and no solid"):
        validate(StationSpec(name="empty", pose=Pose.identity(), super_layers=[]))


def test_the_view_of_a_passive_volume_has_no_super_layers():
    station = Station.from_spec(_wall())

    assert station.super_layers == []
    assert station.bounds[0] == pytest.approx(100.0)
    assert station.bounds[1] == pytest.approx(5.0)


def test_a_passive_volume_sits_in_its_detector():
    detector = DetectorSpec(
        name="MuTel",
        pose=Pose.identity(),
        stations=[_wall(z=-27.0), _wall("LeadWall2", z=27.0)],
        shape=Box(120.0, 120.0, 80.0),
    )

    node = build_detector(detector)

    assert [child.name for child in node.children] == ["LeadWall", "LeadWall2"]
    np.testing.assert_allclose(
        [child.world_pose.translation[2] for child in node.children], [-27.0, 27.0], atol=1e-12
    )
