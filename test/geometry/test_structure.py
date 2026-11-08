"""T-033: detector structure (the yoke) is data, not a node."""

import pytest

from mpldts.geometry import build_detector
from mpldts.geometry.specs import (
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    StructureSpec,
    SuperLayerSpec,
    validate,
)


def _station(name="MB"):
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


def _detector(structure=()):
    return DetectorSpec(
        name="detector",
        pose=Pose.identity(),
        stations=[_station()],
        structure=list(structure),
    )


def _names(node):
    found = [node.name]
    for child in list(node.children) + list(node.attachments):
        found.extend(_names(child))
    return found


def test_structure_validates_and_builds_no_node():
    yoke = StructureSpec("Yoke", Pose.translated(0.0, 0.0, -100.0), Box(100.0, 100.0, 200.0))
    spec = _detector([yoke])

    validate(spec)
    detector = build_detector(spec)

    assert yoke.material == "G4_Fe"
    assert [node.name for node in detector.children] == ["MB"]
    assert detector.attachments == []
    assert "Yoke" not in _names(detector)


def test_a_structure_entry_can_have_no_shape():
    validate(_detector([StructureSpec("Yoke", Pose.identity())]))


def test_structure_is_validated():
    yoke = StructureSpec("Yoke", Pose.identity())
    with pytest.raises(ValueError, match="duplicate structure name"):
        validate(_detector([yoke, yoke]))
    with pytest.raises(ValueError, match="pose must be a Pose"):
        validate(_detector([StructureSpec("Yoke", None)]))
    with pytest.raises(ValueError, match="needs a non-empty name"):
        validate(_detector([StructureSpec("", Pose.identity())]))


def test_a_detector_without_structure_is_unchanged():
    spec = _detector()

    assert spec.structure == []
    assert [node.name for node in build_detector(spec).children] == ["MB"]
