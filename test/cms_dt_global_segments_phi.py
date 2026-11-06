import matplotlib.pyplot as plt
from mpldts.geometry import Station, AMDTSegments
from mpldts.patches import DTStationPatch, DTSegmentsPatch
from matplotlib.colors import BoundaryNorm
import numpy as np

dpi = 100  # Plot resolution

segs_kwargs = {
    "linewidth": 2 * 72 / dpi,
    "color": "green",
}
colors = ['purple', 'orange', 'blue']

# create a set of segments easy to identify for testing purposes
positions = range(-150, 151, 50)
angles  = np.linspace(-0.5, .51, len(positions))
num_segments = len(positions)
sl_values = [1] * (num_segments // 3) + [0] * (num_segments // 3) + [3] * (num_segments - 2 * (num_segments // 3))

segments_info = [
    {"index": i, "sl": sl, "angle": np.degrees(angle), "position": x}
    for i, (angle, x, sl) in enumerate(zip(angles, positions, sl_values), start=1)
]

# Create figure and subplots
fig, axs = plt.subplots(1, 3, figsize=(10, 5), dpi=dpi)
axs  = axs.flatten()

for i, (ax, ref_frame) in enumerate(zip(axs, ["Station", "SectorRef", "SL13Center"])):
    # Define DT station here because can be passed as a parent to segments
    station = Station(wheel=0, sector=1, station=3)
    width, height, length = station.bounds

    for seg_info in segments_info:
        seg_info["parent"] = station

    # Create segments with the provided information
    segments = AMDTSegments(segs_info=segments_info, reference_frame=ref_frame)

    # Create patches for phi-view and eta-view
    _ = DTStationPatch(station, axes=ax, faceview="phi", local=False)

    _ = DTSegmentsPatch(segments, axes=ax, faceview="phi", local=False, segs_kwargs=segs_kwargs)

    # Draw a dot in the the reference frames
    x,y,_ = station.transformer.transform((0, 0, 0), from_frame=ref_frame, to_frame="CMS")
    ax.plot(x, y, 'o', color=colors[i], label=ref_frame + ' Center')
    # add reference lines
    ax.hlines(y, x-height / 2, x + height / 2, color=colors[i], linestyles='dashed', linewidth=2)

    # Add text annotations for the segments
    for i, xs in enumerate(positions, start=1):
        _xs, _ys, _ = station.transformer.transform((xs+2, 0, 0), from_frame=ref_frame, to_frame="CMS")
        ax.text(_xs, _ys, f'idx={i}', ha='center', va='top', fontsize=8)

    # # Set axis limits for phi-view
    ax.set_xlim(580, 650)
    ax.set_ylim(-150, 200)
    ax.set_title(f"Ref Frame: {ref_frame}")
    # Add labels and legend
    ax.set_xlabel("x [cm]")
    ax.set_ylabel("y [cm]")
    ax.set_aspect('equal')
    ax.legend(loc='upper left', fontsize=5)

# Add title
fig.suptitle(f"Segments in DT Station : {station.name} - phi-view (global)", fontsize=12)
plt.show()
fig.savefig("test_cms_dt_global_segments_phi.png", dpi=dpi)
