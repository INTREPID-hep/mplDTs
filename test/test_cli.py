"""The thin command line (info / convert / plot)."""

from dataclasses import replace

from mpldts.cli import main
from mpldts.geometry.constructors import make_layer, make_station, make_superlayer
from mpldts.geometry.serialize import from_json, to_json
from mpldts.geometry.specs import Box, CellGrid, DetectorSpec, Pose


def _document(directory):
    """A small authored station written as a JSON document."""
    layers = [
        make_layer(
            number,
            CellGrid(pitch=20.0, count=8, shape=Box(20.0, 100.0, 1.3), material="GasMixture"),
            pose=Pose.translated(0.0, 0.0, (number - 2.5) * 2.0),
        )
        for number in range(1, 5)
    ]
    super_layers = [
        make_superlayer(
            number,
            layers,
            pose=Pose.rotated_z(90.0 if number == 2 else 0.0, (0.0, 0.0, (number - 2) * 9.5)),
        )
        for number in range(1, 4)
    ]
    station = make_station("testbeam chamber", super_layers, shape=Box(160.0, 100.0, 37.3))
    path = directory / "station.json"
    path.write_text(to_json(station))
    return path


def test_info_prints_the_document(tmp_path, capsys):
    assert main(["info", str(_document(tmp_path))]) == 0

    out = capsys.readouterr().out
    assert "testbeam chamber" in out
    assert "box 160.0 x 100.0 x 37.3 cm" in out
    assert "96 cells" in out
    assert "SL2: 8,8,8,8 cells per layer" in out


def test_convert_writes_the_tg(tmp_path):
    document = _document(tmp_path)
    output = tmp_path / "station.tg"

    assert main(["convert", str(document), str(output)]) == 0

    text = output.read_text()
    assert ":VOLU testbeam_chamber Solid_testbeam_chamber G4_AIR" in text
    assert ":PLACE testbeam_chamber 1 world R0" in text
    assert len([line for line in text.splitlines() if line.startswith(":PLACE")]) == 97


def test_plot_writes_an_svg(tmp_path):
    document = _document(tmp_path)
    output = tmp_path / "station.svg"

    assert main(["plot", str(document), str(output)]) == 0

    text = output.read_text()
    assert text.startswith("<?xml")
    assert len(text) > 10000  # the cells and the station outline are drawn


def test_a_detector_document_picks_one_station(tmp_path):
    station = from_json(_document(tmp_path).read_text())
    detector = DetectorSpec(
        name="TB",
        pose=Pose.identity(),
        stations=[station, replace(station, name="second station")],
        shape=Box(400.0, 400.0, 400.0),
    )
    document = tmp_path / "detector.json"
    document.write_text(to_json(detector))
    output = tmp_path / "second.tg"

    assert main(["convert", str(document), str(output), "--station", "1"]) == 0

    text = output.read_text()
    assert ":VOLU second_station Solid_second_station G4_AIR" in text
    assert ":VOLU testbeam_chamber" not in text


def test_a_detector_document_exports_whole_or_one(tmp_path, capsys):
    station = from_json(_document(tmp_path).read_text())
    detector = DetectorSpec(
        name="TB",
        pose=Pose.identity(),
        stations=[station, replace(station, name="second station")],
        shape=Box(400.0, 400.0, 400.0),
    )
    document = tmp_path / "detector.json"
    document.write_text(to_json(detector))

    assert main(["info", str(document)]) == 0  # info summarises every station
    assert "2 stations" in capsys.readouterr().out

    everything = tmp_path / "all.tg"
    assert main(["convert", str(document), str(everything)]) == 0
    assert ":VOLU TB Solid_TB G4_Galactic" in everything.read_text()

    # a plot is one station: the index is required when there are several
    assert main(["plot", str(document), str(tmp_path / "x.svg")]) == 2
    assert "choose one with --station" in capsys.readouterr().err


def test_a_missing_document_is_one_line_on_stderr(tmp_path, capsys):
    assert main(["info", str(tmp_path / "nope.json")]) == 2

    assert "No such file" in capsys.readouterr().err


def test_a_bad_document_is_one_line_on_stderr(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{not json")

    assert main(["info", str(path)]) == 2

    assert "not JSON" in capsys.readouterr().err
