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

# Define DT station here because can be passed as a parent to segments
station = Station(wheel=2, sector=4, station=3)
width, height, length = station.bounds

# create a set of segments easy to identify for testing purposes
positions = range(-100, 101, 25)
angles  = np.linspace(-0.5, .51, len(positions))
num_segments = len(positions)

segments_info = [
    {"index": i, "parent": station, "sl": 2, "angle": np.degrees(angle), "position": x}
    for i, (angle, x) in enumerate(zip(angles, positions), start=1)
]

# Create figure and subplots
fig, axs = plt.subplots(2, 1, figsize=(10, 5), dpi=dpi)
axs  = axs.flatten()

colors = ['purple', 'orange', 'blue']
for i, (ax, ref_frame) in enumerate(zip(axs, ["Station", "SL13Center"])):
    # Create segments with the provided information
    segments = AMDTSegments(segs_info=segments_info, reference_frame=ref_frame)

    # Create patches for eta-view
    _ = DTStationPatch(station, axes=ax, faceview="eta", local=True, inverted=False)

    _ = DTSegmentsPatch(segments, axes=ax, faceview="eta", local=True, inverted=False, segs_kwargs=segs_kwargs)

    # Draw a dot in the the reference frames
    _, y, z = station.transformer.transform((0, 0, 0), from_frame=ref_frame, to_frame="Station")
    x = -y
    ax.plot(x, z, 'o', color=colors[i], label=ref_frame + ' Center')
    # add reference lines
    ax.vlines(x, -height / 2, height / 2, color=colors[i], linestyles='dashed', linewidth=1)

    # Add text annotations for the segments
    for i, xs in enumerate(positions, start=1):
        _xs = -1 * station.transformer.transform((xs+2, 0, 0), from_frame=ref_frame, to_frame="Station")[1]
        ax.text(_xs, 0, f'idx={i}', ha='center', va='top', fontsize=8)

    # Set axis limits for phi-view
    ax.set_xlim(- length / 2 - 5, length / 2 + 5)
    ax.set_ylim(- height / 2 - 5, height / 2 + 5)

    # Add labels and legend
    ax.set_xlabel("y [cm]")
    ax.set_ylabel("z [cm]")
    ax.set_aspect('equal')
    ax.legend(loc='upper left', fontsize=5)

# Add title
fig.suptitle(f"Segments in DT Station : {station.name}- eta-view (local)", fontsize=12)
plt.show()
fig.savefig("test_cms_dt_local_segments_eta.png", dpi=dpi)
