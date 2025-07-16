import matplotlib.pyplot as plt
from mpldts.geometry import Station, AMDTSegments
from mpldts.patches import DTStationPatch, DTSegmentsPatch
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

# Define DT station here because can be passed as a parent to segments
station = Station(wheel=2, sector=1, station=3)

segments_info = [
    {"index": 1, "parent": station, "sl": 3, "angle": 1, "position": -100, "q": 1},
    {"index": 2, "parent": station, "sl": 3, "angle": 0.2, "position": -50, "q": 2},
    {"index": 3, "parent": station, "sl": 3, "angle": 0.05, "position": 0, "q": 3},
    {"index": 4, "parent": station, "sl": 1, "angle": 30, "position": -15, "q": 2},
    {"index": 5, "parent": station, "sl": 1, "angle": -7, "position": -75, "q": 7},
    {"index": 6, "parent": station, "sl": 1, "angle": 8, "position": 2, "q": 8},
    {"index": 7, "parent": station, "sl": 2, "angle": 20, "position": -30, "q": 4},
    {"index": 8, "parent": station, "sl": 2, "angle": -5, "position": 20, "q": 5},
    {"index": 9, "parent": station, "sl": 2, "angle": 6, "position": -10, "q": 6},
]


# Create figure and subplots
fig, axs = plt.subplots(1, 2, figsize=(15, 7), sharey=True, dpi=dpi)

# Create segments with the provided information
segments = AMDTSegments(segs_info=segments_info)

# Create patches for phi-view and eta-view
dt_patch_phi = DTStationPatch(station, axes=axs[0], faceview="phi", local=True, inverted=False)
dt_patch_eta = DTStationPatch(station, axes=axs[1], faceview="eta", local=True, inverted=False)
segs_patch_phi = DTSegmentsPatch(
    segments, axes=axs[0], faceview="phi", local=True, inverted=False, vmap="q",
    segs_kwargs=segs_kwargs
)
segs_patch_eta = DTSegmentsPatch(
    segments, axes=axs[1], faceview="eta", local=True, inverted=False, vmap="q",
    segs_kwargs=segs_kwargs
)

# Move the colorbar to a separate part of the figure
cbar_ax = fig.add_axes([0.9, 0.09, 0.02, 0.8])  # Define a new axis for the colorbar
fig.colorbar(segs_patch_phi.segments_collection, cax=cbar_ax, label="Segment Quality")

# Draw the AM Trigger primitves reference frame
width, height, length = station.bounds

TPsFrame_center = station.transformer.transform([0,0,0], from_frame="TPsFrame", to_frame="Station")

axs[0].vlines(TPsFrame_center[0], - height / 2 , height / 2, color='black', linewidth=1, alpha=0.7, linestyle='dashed')
axs[0].hlines(TPsFrame_center[2], - width / 2, width / 2, color='black', linewidth=1, alpha=0.7, linestyle='dashed')
axs[1].vlines(-TPsFrame_center[1], - height / 2, height / 2, color='black', linewidth=1, alpha=0.7, linestyle='dashed')
axs[1].hlines(TPsFrame_center[2], -length/2, length/2, color='black', linewidth=1, alpha=0.7, linestyle='dashed')

axs[0].vlines(0, - height / 2 , height / 2, color='red', linewidth=1, alpha=0.7, linestyle='dashed')
axs[0].hlines(0, - width / 2, width / 2, color='red', linewidth=1, alpha=0.7, linestyle='dashed')
axs[1].vlines(0, - height / 2, height / 2, color='red', linewidth=1, alpha=0.7, linestyle='dashed')
axs[1].hlines(0, -length/2, length/2, color='red', linewidth=1, alpha=0.7, linestyle='dashed')

for seg in segments:
    print(seg.number, " -> ", seg.local_center)

# Set axis limits for phi-view
x, y, z = station.local_center
axs[0].set_xlim(x - width / 2 - 5, x + width / 2 + 5)
axs[0].set_ylim(z - height / 2 - 5, z + height / 2 + 5)

# Set axis limits for eta-view
axs[1].set_xlim(y - length / 2 - 5, y + length / 2 + 5)
axs[1].set_ylim(z - height / 2 - 5, z + height / 2 + 5)

# Add titles and labels
fig.suptitle(f"Segments in DT Station : {station.name}")
axs[0].set_title(r"$\phi$-view")
axs[1].set_title(r"$\eta$-view")
axs[0].set_xlabel("x [cm]")
axs[0].set_ylabel("z [cm]")
axs[1].set_xlabel("x [cm]")

plt.tight_layout(rect=[0, 0, 0.9, 1])  # Adjust layout to make room for the colorbar
plt.show()
# fig.savefig("./cms_dt_segments_inverted.svg", dpi=dpi)