"""A thin command line for the authoring path.

    mpldts info    station.json
    mpldts convert station.json out.tg    [--station N]
    mpldts plot    station.json out.svg   [--station N]

Each command is a couple of calls into the library: the JSON document becomes a
spec, the spec becomes a node tree, and the tree becomes a .tg file or a plot.
No configuration files, no plugin discovery, no framework: three subcommands
that save writing a five-line script per conversion.

Errors are one line on stderr and a non-zero exit code, never a traceback.
"""

import argparse
import sys

from mpldts.geometry import Station, build_detector, build_station
from mpldts.geometry.serialize import from_json
from mpldts.geometry.specs import DetectorSpec

PROGRAM = "mpldts"


# -- the document ----------------------------------------------------------


def _read(path):
    """The spec in the JSON document at path."""
    try:
        with open(path) as handle:
            text = handle.read()
    except OSError as error:
        raise ValueError("%s: %s" % (path, error.strerror or error)) from None
    return from_json(text)


def _station_of(spec, index=None):
    """One station: the document itself, or station index of a detector."""
    if not isinstance(spec, DetectorSpec):
        return spec
    stations = spec.stations
    if index is None:
        if len(stations) != 1:
            raise ValueError(
                "the document holds %d stations: choose one with --station"
                % len(stations)
            )
        return stations[0]
    if not 0 <= index < len(stations):
        raise ValueError(
            "--station %d is out of range (0..%d)" % (index, len(stations) - 1)
        )
    return stations[index]


def _cells(spec):
    return sum(layer.cells.count for sl in spec.super_layers for layer in sl.layers)


def _shape(shape):
    if shape is None:
        return "no solid"
    values = getattr(shape, "dx", None)
    if values is not None:
        return "box %.1f x %.1f x %.1f cm" % (shape.dx, shape.dy, shape.dz)
    return "tube r=%.1f length=%.1f cm along %s" % (shape.radius, shape.length, shape.axis)


def _describe(station, indent=""):
    lines = [
        "%s%s  material %s" % (indent, station.name, station.material),
        "%s  %s" % (indent, _shape(station.shape)),
        "%s  %d super layers, %d layers, %d cells, %d attachments"
        % (
            indent,
            len(station.super_layers),
            sum(len(sl.layers) for sl in station.super_layers),
            _cells(station),
            len(station.attachments),
        ),
    ]
    for super_layer in station.super_layers:
        lines.append(
            "%s  SL%d: %s cells per layer"
            % (
                indent,
                super_layer.number,
                ",".join(str(layer.cells.count) for layer in super_layer.layers),
            )
        )
    return lines


# -- the commands ----------------------------------------------------------


def command_info(spec, options):
    """Print what a document holds: names, bounds, materials, cell counts."""
    if isinstance(spec, DetectorSpec):
        lines = ["detector %s  %s" % (spec.name, _shape(spec.shape))]
        for station in spec.stations:
            lines.extend(_describe(station, "  "))
        lines.append("  %d stations" % len(spec.stations))
    else:
        lines = _describe(spec)
    print("\n".join(lines))
    return 0


def command_convert(spec, options):
    from mpldts.export import TgSink, export_volumes, iter_volume_placements

    node = (
        build_detector(spec)
        if isinstance(spec, DetectorSpec) and options.station is None
        else build_station(_station_of(spec, options.station))
    )
    export_volumes(node, TgSink(options.output))
    print(
        "%s: %d volumes"
        % (options.output, sum(1 for _ in iter_volume_placements(node)))
    )
    return 0


def command_plot(spec, options):
    import matplotlib.pyplot as plt

    from mpldts.patches import DTStationPatch

    view = Station.from_spec(_station_of(spec, options.station))
    x, y, z = view.local_center
    width, thickness, length = view.bounds
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=100)
    for axis, faceview in zip(axes, ("phi", "eta")):
        DTStationPatch(view, axis, faceview=faceview, local=True)
        if faceview == "phi":
            axis.set_xlim(x - width / 2 - 5.0, x + width / 2 + 5.0)
        else:
            axis.set_xlim(y - length / 2 - 5.0, y + length / 2 + 5.0)
        axis.set_ylim(z - thickness / 2 - 5.0, z + thickness / 2 + 5.0)
        axis.set_title("%s view" % faceview)
        axis.set_xlabel("cm")
        axis.set_ylabel("cm")
    figure.suptitle(view.name)
    figure.tight_layout()
    figure.savefig(options.output, dpi=100)
    plt.close(figure)
    print("%s: phi and eta views" % options.output)
    return 0


COMMANDS = {"info": command_info, "convert": command_convert, "plot": command_plot}


# -- the entry point -------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(prog=PROGRAM, description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name, function in COMMANDS.items():
        command = commands.add_parser(name, help=function.__doc__)
        command.add_argument("document", help="a JSON station or detector document")
        if name != "info":
            command.add_argument("output", help="the file to write")
        command.add_argument(
            "--station",
            type=int,
            metavar="N",
            help="index of the station to use in a detector document",
        )
    options = parser.parse_args(argv)

    try:
        spec = _read(options.document)
        return COMMANDS[options.command](spec, options)
    except (ValueError, OSError) as error:
        print("%s: %s" % (PROGRAM, error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
