"""A station that is not in the CMS XML: one and five super layers (T-030).

The geometry is described with specs only. Station.from_spec gives the same
legacy views, and therefore the same plotting patches, as a CMS chamber.
"""

import matplotlib.pyplot as plt

from mpldts.geometry import Station, build_detector
from mpldts.geometry.specs import (
    Box,
    CellGrid,
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
)
from mpldts.patches import DTStationPatch

DPI = 100


def layers():
    """Four layers of eight cells (4 cm pitch, 8 cm long, 1.3 cm thick)."""
    return [
        LayerSpec(
            number=number,
            pose=Pose.translated(0.0, 0.0, (number - 2.5) * 2.5),
            cells=CellGrid(pitch=4.0, count=8, shape=Box(4.0, 8.0, 1.3)),
        )
        for number in range(1, 5)
    ]


def station_spec(name, number_of_super_layers, pose):
    """A super layer every 9.5 cm along z, centred on the station frame."""
    centre = (number_of_super_layers - 1) / 2.0
    super_layers = [
        SuperLayerSpec(
            number=number,
            pose=Pose.translated(0.0, 0.0, (number - 1 - centre) * 9.5),
            layers=layers(),
            shape=Box(32.0, 8.0, 8.8),
        )
        for number in range(1, number_of_super_layers + 1)
    ]
    return StationSpec(
        name=name,
        pose=pose,
        super_layers=super_layers,
        shape=Box(32.0, 8.0, (number_of_super_layers - 1) * 9.5 + 8.8),
    )


# One detector, two stations: the assembly is a single node tree
detector = DetectorSpec(
    name="two custom chambers",
    pose=Pose.identity(),
    stations=[
        station_spec("one_sl", 1, Pose.rotated_z(30.0, (100.0, 0.0, 0.0))),
        station_spec("five_sl", 5, Pose.rotated_z(-45.0, (-100.0, 0.0, 0.0))),
    ],
)
detector_node = build_detector(detector)
print([station.name for station in detector_node.children])

figure, axes = plt.subplots(2, 2, figsize=(13, 10), dpi=DPI)
for row, spec in enumerate(detector.stations):
    station = Station.from_spec(spec)
    width, height, length = station.bounds
    x, y, z = station.local_center
    for column, faceview in enumerate(("phi", "eta")):
        axis = axes[row][column]
        DTStationPatch(station, axis, faceview=faceview, local=True)
        if faceview == "phi":
            axis.set_xlim(x - width / 2 - 5.0, x + width / 2 + 5.0)
        else:
            axis.set_xlim(y - length / 2 - 5.0, y + length / 2 + 5.0)
        axis.set_ylim(z - height / 2 - 5.0, z + height / 2 + 5.0)
        axis.set_title("%s: %s view" % (station.name, faceview))
        axis.set_xlabel("x [cm]")
        axis.set_ylabel("z [cm]")

figure.suptitle("Stations built from a spec (1 and 5 super layers)")
plt.tight_layout()
plt.show()
figure.savefig("./custom_station.svg", dpi=DPI)
