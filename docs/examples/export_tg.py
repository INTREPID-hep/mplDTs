"""Author a station, save it as JSON and export it as a .tg file (Phase 5).

The whole authoring path: build the spec with the short constructors, write the
JSON document, read the document back, build the node tree from it, plot the
chamber, and export the volumes for Geant4.

The .tg file is the format DTG4Simulator reads with G4tgbVolumeMgr; it holds the
placements only, so it is included from a document that defines the world volume
and the identity rotation R0.
"""

import matplotlib.pyplot as plt

from mpldts.export import TgSink, export_volumes, iter_volume_placements
from mpldts.geometry import Station, build_station
from mpldts.geometry.builders import make_layer, make_station, make_superlayer
from mpldts.geometry.serialize import from_json, to_json
from mpldts.geometry.specs import Box, CellGrid, Pose
from mpldts.patches import DTStationPatch

DPI = 100
PITCH = 20.0


def layers():
    """Four layers of eight long cells, 2 cm apart along z."""
    return [
        make_layer(
            number,
            CellGrid(pitch=PITCH, count=8, shape=Box(PITCH, 100.0, 1.3), material="GasMixture"),
            pose=Pose.translated(0.0, 0.0, (number - 2.5) * 2.0),
        )
        for number in range(1, 5)
    ]


def super_layers():
    """Three super layers every 9.5 cm, the middle one turned by 90 degrees."""
    return [
        make_superlayer(
            number,
            layers(),
            pose=Pose.rotated_z(90.0 if number == 2 else 0.0, (0.0, 0.0, (number - 2) * 9.5)),
        )
        for number in range(1, 4)
    ]


station = make_station(
    "testbeam chamber",
    super_layers(),
    shape=Box(8 * PITCH, 100.0, 3 * 9.5 + 8.8),
)

# 1. The document: poses, shapes and names, nothing derived. Read it back and
# the station is the same one, so the file can be edited by hand.
document = to_json(station)
with open("./testbeam_station.json", "w") as handle:
    handle.write(document)
restored = from_json(document)
print("station:", restored.name, " (%d bytes of JSON)" % len(document))
print("super layers:", [sl.number for sl in restored.super_layers])

# 2. The node tree: the same builder the CMS chambers use. Only the station
# and the cells are solids; super layers and layers are grouping frames.
node = build_station(restored)
print("volumes:", len(list(iter_volume_placements(node))))

# 3. The geometry for Geant4: one solid per super layer, one placement per cell.
export_volumes(node, TgSink("./testbeam_station.tg"))
print("wrote ./testbeam_station.tg")

# 4. The plots: the legacy patches work on a station that is not in the XML.
view = Station.from_spec(restored)
width, height, length = view.bounds
x, y, z = view.local_center
figure, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=DPI)
for axis, faceview in zip(axes, ("phi", "eta")):
    DTStationPatch(view, axis, faceview=faceview, local=True)
    if faceview == "phi":
        axis.set_xlim(x - width / 2 - 5.0, x + width / 2 + 5.0)
    else:
        axis.set_xlim(y - length / 2 - 5.0, y + length / 2 + 5.0)
    axis.set_ylim(z - height / 2 - 5.0, z + height / 2 + 5.0)
    axis.set_title("%s view" % faceview)
    axis.set_xlabel("x [cm]")
    axis.set_ylabel("z [cm]")
figure.suptitle("Authored station: JSON in, plot and .tg out")
plt.tight_layout()
plt.show()
figure.savefig("./testbeam_station.svg", dpi=DPI)
