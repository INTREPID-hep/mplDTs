"""T-052: the volume sink, the .tg writer and its parity with the generator."""

import io
import os
from dataclasses import replace

import numpy as np
import pytest

from mpldts.export import (
    RecordingSink,
    TgFormatError,
    TgSink,
    export_volumes,
    iter_volume_placements,
)
from mpldts.geometry import Station, build_detector, build_station
from mpldts.geometry.sources import CMSXMLSource
from mpldts.geometry.specs import (
    AttachmentSpec,
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
    Tube,
)

#: Output of generate_geometry_data.py for (0, 1, 1) in DTG4Simulator; the
#: parity oracle of T-052. Override with MPLDTS_TG_REFERENCE.
REFERENCE = os.environ.get(
    "MPLDTS_TG_REFERENCE",
    "/home/destrada/Geant4/DTG4Simulator/geometry/stations/station_W0_Sec1_St1.tg",
)

_SOLID_KINDS = {"BOX", "TUBE", "TUBS", "TRD1", "TRD2", "TRAP", "ORB", "TUBE"}


def _parse(text):
    """(solids, volumes, rotations, placements) of a .tg document."""
    rotations = {"R0": np.eye(3)}
    solids, volumes, placements = {}, {}, []
    for line in text.splitlines():
        tokens = line.split()
        if not tokens or tokens[0].startswith("//"):
            continue
        head = tokens[0]
        if head == ":ROTM":
            values = [float(value) for value in tokens[2:]]
            if len(values) == 9:
                rotations[tokens[1]] = np.array(values).reshape(3, 3)
        elif head == ":SOLID":
            solids[tokens[1]] = (
                tokens[2],
                tuple(float(value.split("*")[0]) for value in tokens[3:6]),
            )
        elif head == ":VOLU":
            name, second = tokens[1], tokens[2]
            if second in _SOLID_KINDS:  # solid defined inline
                solids["<" + name + ">"] = (
                    second,
                    tuple(float(value.split("*")[0]) for value in tokens[3:6]),
                )
                volumes[name] = ("<" + name + ">", tokens[-1])
            else:
                volumes[name] = (second, tokens[3])
        elif head == ":PLACE":
            placements.append(
                (
                    tokens[1],
                    tokens[3],
                    tokens[4],
                    np.array([float(value.split("*")[0]) for value in tokens[5:8]]),
                )
            )
    return solids, volumes, rotations, placements


def _facts(solids, volumes, rotations, placements):
    """Placements as backend-neutral facts: solid, dimensions, material, rotation."""
    facts = []
    for name, mother, rotation, position in placements:
        solid, material = volumes[name]
        kind, dimensions = solids[solid]
        facts.append(
            (
                kind,
                tuple(round(value, 4) for value in dimensions),
                material,
                np.round(rotations[rotation], 6),
                np.round(position, 4),
            )
        )
    return facts


def _tg(root):
    stream = io.StringIO()
    export_volumes(root, TgSink(stream))
    return stream.getvalue()


def _station(name="station", cells=None, attachments=(), pose=None, material=None):
    cells = CellGrid(pitch=4.0, count=4, shape=Box(4.0, 8.0, 1.3), material=material) if cells is None else cells
    return StationSpec(
        name=name,
        pose=Pose.identity() if pose is None else pose,
        super_layers=[
            SuperLayerSpec(
                number=1,
                pose=Pose.translated(0.0, 0.0, 5.0),
                layers=[
                    LayerSpec(number=1, pose=Pose.translated(0.0, 0.0, 0.0), cells=cells),
                    LayerSpec(number=2, pose=Pose.translated(0.0, 0.0, -1.3), cells=cells),
                ],
            )
        ],
        shape=Box(40.0, 70.0, 12.0),
        material="G4_AIR",
        attachments=list(attachments),
    )


# -- the seam -------------------------------------------------------------


def test_the_walk_folds_grouping_frames_into_the_placements():
    station = _station(material="GasMixture")
    root = build_station(station)

    placements = list(iter_volume_placements(root))

    assert len(placements) == 1 + 8  # station and two layers of four cells
    assert placements[0].node is root and placements[0].mother is None
    assert placements[0].pose_in_mother.translation == pytest.approx((0.0, 0.0, 0.0))
    for placement in placements[1:]:
        assert placement.mother is root
        assert placement.node.kind == "cell"
    # the folded pose keeps the super layer and layer offsets
    np.testing.assert_allclose(placements[1].pose_in_mother.translation, (-6.0, 0.0, 5.0))
    np.testing.assert_allclose(placements[5].pose_in_mother.translation, (-6.0, 0.0, 3.7))


def test_attachments_are_volumes_placed_after_the_cells():
    panel = AttachmentSpec(
        name="Honeycomb",
        pose=Pose.translated(0.0, 0.0, 1.0),
        shape=Box(39.0, 69.0, 2.0),
    )
    root = build_station(_station(material="GasMixture", attachments=[panel]))

    placements = list(iter_volume_placements(root))

    assert placements[-1].node.kind == "attachment"
    assert placements[-1].mother is root
    np.testing.assert_allclose(placements[-1].pose_in_mother.translation, (0.0, 0.0, 1.0))


def test_the_recording_sink_sees_exactly_the_walk():
    root = build_station(_station(material="GasMixture"))
    sink = RecordingSink()

    export_volumes(root, sink)

    assert sink.root is root
    expected = list(iter_volume_placements(root))
    assert len(sink.placements) == len(expected)
    for got, want in zip(sink.placements, expected):
        assert got.node is want.node and got.mother is want.mother
        np.testing.assert_allclose(got.pose_in_mother.matrix(), want.pose_in_mother.matrix())


def test_a_detector_builds_into_one_graph_and_exports():
    station = _station(name="A", material="GasMixture")
    detector = DetectorSpec(
        name="TB",
        pose=Pose.rotated_z(15.0, (10.0, -20.0, 30.0)),
        stations=[station],
        shape=Box(200.0, 200.0, 200.0),
    )
    root = build_detector(detector)
    stream = io.StringIO()

    export_volumes(root, TgSink(stream))
    text = stream.getvalue()

    assert ":VOLU TB Solid_TB G4_Galactic" in text
    assert ":PLACE TB 1 world RM_TB_1 10.000000*cm -20.000000*cm 30.000000*cm" in text
    assert ":PLACE A 1 TB R0 0.000000*cm 0.000000*cm 0.000000*cm" in text
    solids, volumes, rotations, placements = _parse(text)
    np.testing.assert_allclose(  # the world rotation on the root placement
        rotations["RM_TB_1"] @ (1.0, 0.0, 0.0), (0.9659258, 0.2588190, 0.0), atol=1e-6
    )


# -- the .tg writer -------------------------------------------------------


def test_the_tg_places_every_cell_at_its_xml_centre():
    source = CMSXMLSource()
    spec = source.station(0, 1, 1)
    reference = spec.pose  # the exporter below writes in the station frame
    exported = build_station(replace(spec, name="Station_W0_Sec1_St1", pose=Pose.identity()))

    text = _tg(exported)
    solids, volumes, rotations, placements = _parse(text)

    centres = source.cell_centres(0, 1, 1)
    order = [
        (sl.number, layer.number, number)
        for sl in spec.super_layers
        for layer in sl.layers
        for number in layer.cells.ids()
    ]
    assert len(placements) == 1 + len(order)
    for placement, key in zip(placements[1:], order):
        world = reference.apply(placement[3])
        np.testing.assert_allclose(world, centres[key], atol=1e-3)
    assert len(volumes) == 4  # station plus one cell volume per super layer
    assert len(rotations) == 2  # identity and the 90 degree super layer 2


@pytest.mark.skipif(not os.path.exists(REFERENCE), reason="DTG4Simulator checkout not available")
def test_the_tg_matches_the_current_generator():
    source = CMSXMLSource()
    spec = source.station(0, 1, 1)
    exported = build_station(replace(spec, name="Station_W0_Sec1_St1", pose=Pose.identity()))

    with open(REFERENCE) as handle:
        expected = _facts(*_parse(handle.read()))
    produced = _facts(*_parse(_tg(exported)))

    assert len(produced) == len(expected) == 621
    for want, got in zip(expected, produced):
        assert got[0] == want[0] and got[1] == want[1] and got[2] == want[2]  # solid, material
        np.testing.assert_allclose(got[3], want[3], atol=1e-6)  # rotation
        np.testing.assert_allclose(got[4], want[4], atol=1e-4)  # position in cm


def test_a_tube_cell_is_rotated_onto_its_axis():
    grid = CellGrid(pitch=3.0, count=3, shape=Tube(radius=1.2, length=100.0, axis="y"), material="GasMixture")
    root = build_station(_station(cells=grid, pose=Pose.rotated_z(30.0, (10.0, 20.0, 30.0))))

    text = _tg(root)
    solids, volumes, rotations, placements = _parse(text)

    assert ":SOLID Solid_DriftCell_station_SL1 TUBE 0.000000*cm 1.200000*cm 50.000000*cm" in text
    for placement in placements[1:]:
        # the Geant4 tube is built along +z: the placement turns it onto +y
        np.testing.assert_allclose(rotations[placement[2]] @ (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), atol=1e-9)


def test_copy_numbers_are_unique_within_a_mother():
    panel = AttachmentSpec(
        name="Honeycomb",
        pose=Pose.translated(0.0, 0.0, 1.0),
        shape=Box(39.0, 69.0, 2.0),
    )
    root = build_station(_station(material="GasMixture", attachments=[panel]))

    text = _tg(root)

    copies = {}
    for line in text.splitlines():
        if line.startswith(":PLACE"):
            tokens = line.split()
            copies.setdefault(tokens[3], []).append(int(tokens[2]))

    assert copies["world"] == [1]
    assert sorted(copies["station"]) == list(range(1, 10))  # 8 cells then the panel


def test_a_volume_without_a_material_is_rejected():
    root = build_station(_station())  # the cell grid carries no material

    with pytest.raises(TgFormatError, match="has no material"):
        _tg(root)


def test_names_are_safe_for_geant4_and_unique_per_file():
    station = _station(name="TB-2026 / station 1", material="GasMixture")
    text = _tg(build_station(station))

    assert ":VOLU TB_2026___station_1 Solid_TB_2026___station_1 G4_AIR" in text
    assert ":VOLU DriftCell_TB_2026___station_1_SL1 Solid_DriftCell_TB_2026___station_1_SL1 GasMixture" in text


def test_the_world_volume_is_not_written():
    text = _tg(build_station(_station(material="GasMixture")))

    assert ":VOLU world" not in text
    assert ":PLACE station 1 world" in text
