"""T-050: the short constructors for hand-written specs."""

import pytest

from mpldts.geometry import build_detector
from mpldts.geometry.constructors import make_detector, make_layer, make_station, make_superlayer
from mpldts.geometry.serialize import to_dict
from mpldts.geometry.specs import (
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
    validate,
)


def _grid():
    return CellGrid(pitch=4.2, count=24, shape=Box(4.2, 120.0, 1.3), material="GasMixture")


def test_the_builders_fill_the_defaults():
    layer = make_layer(1, _grid())
    super_layer = make_superlayer(2, [layer])
    station = make_station("TB-1", [super_layer])

    assert layer.pose.rotation == pytest.approx(Pose.identity().rotation)
    assert layer.shape is None and layer.material is None
    assert super_layer.pose.translation == pytest.approx((0.0, 0.0, 0.0))
    assert station.material == "G4_AIR"
    assert station.attachments == []
    assert station.shape is None


def test_a_built_spec_is_the_same_document_as_the_long_hand_written_one():
    layer = make_layer(1, _grid(), pose=Pose.translated(0.0, 0.0, 1.95))
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
                                cells=_grid(),
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
