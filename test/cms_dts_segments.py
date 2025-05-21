import matplotlib.pyplot as plt
from mpldts.geometry import Station, AMDTSegments
from mpldts.patches import MultiDTSegmentsPatch, DTStationPatch
from matplotlib.colors import BoundaryNorm

dpi = 100  # Plot resolution

# Configure colormap and normalization for the plot
cmap = plt.get_cmap('viridis', 9)  # Ensure the colormap has 9 discrete colors
cmap.set_under('none')  # Set color for values below the minimum
quality_norm = BoundaryNorm(boundaries=[0.1, 1, 2, 3, 4, 5, 6, 7, 8, 9], ncolors=9, clip=True)

segs_kwargs = {
    "linewidth": 3 * 72 / dpi,
    "cmap": cmap,
    "norm": quality_norm,
}

# Define multiple DT stations
station1 = Station(wheel=2, sector=1, station=3)
station2 = Station(wheel=2, sector=2, station=3)
station3 = Station(wheel=2, sector=3, station=3)

segments_info = [
    {"index": 1, "parent": station1, "sl": 3, "angle": 1, "position": -100, "q": 1},
    {"index": 2, "parent": station1, "sl": 3, "angle": 0.2, "position": -50, "q": 2},
    {"index": 3, "parent": station2, "sl": 3, "angle": 0.05, "position": 0, "q": 3},
    {"index": 4, "parent": station2, "sl": 1, "angle": 30, "position": -15, "q": 2},
    {"index": 5, "parent": station3, "sl": 1, "angle": -7, "position": -75, "q": 7},
    {"index": 6, "parent": station3, "sl": 1, "angle": 8, "position": 2, "q": 8},
]

# Create figure and subplots
fig, axs = plt.subplots(1, 1, figsize=(7, 7), dpi=dpi)

# Create the station patches for each station
dt_patch_station1 = DTStationPatch(station1, axes=axs, faceview="phi", local=False)
dt_patch_station2 = DTStationPatch(station2, axes=axs, faceview="phi", local=False)
dt_patch_station3 = DTStationPatch(station3, axes=axs, faceview="phi", local=False)

# Create segments with the provided information
segments = AMDTSegments(segs_info=segments_info)

# Create patches for each station
segs_patch_station1 = MultiDTSegmentsPatch(
    segments, axes=axs, faceview="phi", local=False, vmap="q",
    segs_kwargs=segs_kwargs
)


# Add titles and labels
axs.set_title("Segments in Multiple DT Stations")

axs.set_xlabel("x [cm]")
axs.set_ylabel("y [cm]")

axs.set_xlim(000, 800)
axs.set_ylim(-200, 700)

plt.show()