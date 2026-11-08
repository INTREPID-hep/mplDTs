"""T-032: honeycomb panels are a station attachment, derived for CMS chambers."""

import numpy as np
import pytest

from mpldts.geometry import Station, build_station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import (
    AttachmentSpec,
    Box,
    CellGrid,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
    validate,
)

#: The chamber the simulator uses as its reference for the honeycomb.
CHAMBER = (-2, 1, 2)


def _cms_station(chamber=CHAMBER):
    return Station.from_spec(CMSXMLSource().station(*chamber), *chamber)


def test_a_cms_chamber_carries_its_honeycomb_panel():
    station = _cms_station()
    panels = station._node.attachments

    assert [panel.name for panel in panels] == ["Honeycomb"]
    panel = panels[0]
    assert panel.kind == "attachment"
    assert panel.material == "G4_Al"
    # as the simulator builds it: the gap between SL1 and SL2, 1 cm clear
    np.testing.assert_allclose(panel.pose.translation, (0.0, 0.0, 2.67499), atol=1e-3)
    assert panel.shape.dx == pytest.approx(265.799988, abs=1e-3)
    assert panel.shape.dy == pytest.approx(250.100006, abs=1e-3)
    assert panel.shape.dz == pytest.approx(11.80002, abs=1e-3)


def test_the_panel_sits_between_the_super_layers():
    source = CMSXMLSource()
    record = source.record(*CHAMBER)
    members = {super_layer["number"]: super_layer for super_layer in record["super_layers"]}
    top = members[1]["local"][2] - members[1]["bounds"][1] / 2.0
    bottom = members[2]["local"][2] + members[2]["bounds"][1] / 2.0

    panel = _cms_station()._node.attachments[0]

    assert bottom < panel.pose.translation[2] < top
    assert panel.shape.dz < top - bottom
    assert panel.shape.volume() > 0.0


def test_an_mb4_chamber_takes_the_third_super_layer():
    source = CMSXMLSource()
    key = next(chamber for chamber in source.chamber_keys() if chamber[2] == 4)
    record = source.record(*key)
    members = {super_layer["number"]: super_layer for super_layer in record["super_layers"]}
    assert 2 not in members

    panel = _cms_station(key)._node.attachments[0]
    expected_z = (
        members[3]["local"][2]
        + members[3]["bounds"][1] / 2.0
        + members[1]["local"][2]
        - members[1]["bounds"][1] / 2.0
    ) / 2.0
    np.testing.assert_allclose(panel.pose.translation[2], expected_z, atol=1e-3)


def test_the_panel_is_a_frame():
    station = _cms_station()

    frame = station.transformer.transform((0.0, 0.0, 0.0), "Honeycomb", "Station")
    np.testing.assert_allclose(frame, (0.0, 0.0, 2.67499), atol=1e-3)


def _station(attachments=()):
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


def test_a_custom_station_carries_only_its_own_attachments():
    panel = AttachmentSpec("Panel", Pose.translated(0.0, 0.0, 5.0), Box(10.0, 10.0, 0.5))
    built = build_station(_station([panel]))
    station = Station.from_spec(_station([panel]))

    assert [node.name for node in built.attachments] == ["Panel"]
    assert [node.name for node in station._node.attachments] == ["Panel"]
    np.testing.assert_allclose(
        station._node.attachments[0].pose.translation, (0.0, 0.0, 5.0), atol=1e-12
    )
    assert station._node.frame_id + "/Panel" in station.transformer.graph.frames()


def test_a_custom_station_without_attachments_has_none():
    assert build_station(_station()).attachments == []
    assert Station.from_spec(_station())._node.attachments == []


def test_attachments_are_validated():
    with pytest.raises(ValueError, match="duplicate attachment name"):
        validate(
            _station(
                [
                    AttachmentSpec("Panel", Pose.identity(), Box(1.0, 1.0, 1.0)),
                    AttachmentSpec("Panel", Pose.identity(), Box(1.0, 1.0, 1.0)),
                ]
            )
        )
    with pytest.raises(ValueError, match="needs a shape"):
        validate(_station([AttachmentSpec("Panel", Pose.identity(), None)]))
