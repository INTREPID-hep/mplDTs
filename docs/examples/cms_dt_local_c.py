import matplotlib.pyplot as plt
from mpldts.geometry import Station
from mpldts.patches import DTStationPatch
from matplotlib.colors import Normalize

dpi = 100  # Plot resolution

# Configure colormap and normalization for the plot
cmap = plt.get_cmap("viridis").copy()
cmap.set_under("none")  # Set color for values below the minimum
norm = Normalize(vmin=0.1, vmax=20)  # Normalize data values to colormap range

# Cell appearance configuration
cells_kwargs = {
    "linewidth": 0.4 * 72 / dpi,
    "edgecolor": "k",
    "cmap": cmap,
    "norm": norm,
}

# Bounds appearance configuration
bounds_kwargs = {
    "linewidth": 72 / dpi,
    "edgecolor": "k",
    # Fill colors for chamber, SL1, SL3, and SL2 in that order
    "facecolor": ["lightgray", "lightyellow", "lightpink", "lightblue"],
    "alpha": 0.3,  # Transparency
}

# Define DT station information (example data)
dt_info = [
    {"sl": 1, "l": 1, "w": 1, "var1": 2},
    {"sl": 1, "l": 2, "w": 1, "var1": 5},
    {"sl": 1, "l": 3, "w": 1, "var1": 10},
    {"sl": 1, "l": 4, "w": 2, "var1": 1},
    {"sl": 2, "l": 1, "w": 1, "var1": 7},
    {"sl": 2, "l": 2, "w": 1, "var1": 3},
    {"sl": 2, "l": 3, "w": 1, "var1": 8},
    {"sl": 2, "l": 4, "w": 2, "var1": 4},
    {"sl": 3, "l": 1, "w": 1, "var1": 6},
    {"sl": 3, "l": 2, "w": 1, "var1": 9},
    {"sl": 3, "l": 3, "w": 1, "var1": 12},
    {"sl": 3, "l": 4, "w": 2, "var1": 17},
]

# Create figure and subplots
fig, axs = plt.subplots(1, 2, figsize=(15, 7), sharey=True, dpi=dpi)
axs = axs.flatten()

# Define DT station
station = Station(wheel=-1, sector=1, station=2, dt_info=dt_info)

# Create patches for phi-view and eta-view
dt_patch_phi = DTStationPatch(
    station,
    axes=axs[0],
    faceview="phi",
    local=True,
    cells_kwargs=cells_kwargs,
    vmap="var1",
    bounds_kwargs=bounds_kwargs,
)
dt_patch_z = DTStationPatch(
    station,
    axes=axs[1],
    faceview="eta",
    local=True,
    cells_kwargs=cells_kwargs,
    vmap="var1",
    bounds_kwargs=bounds_kwargs,
)

# Add colorbar for the variable mapped to cell colors
fig.colorbar(dt_patch_z.cells_collection, label="Arbitrary variable")

# Set axis limits for phi-view
width, height, length = station.bounds
x, y, z = station.local_center
axs[0].set_xlim(x - width / 2 - 5, x + width / 2 + 5)
axs[0].set_ylim(z - height / 2 - 5, z + height / 2 + 5)

# Set axis limits for eta-view
axs[1].set_xlim(y - length / 2 - 5, y + length / 2 + 5)
axs[1].set_ylim(z - height / 2 - 5, z + height / 2 + 5)

# Add titles and labels
fig.suptitle(f"Local view of a DT Station : {station.name}")
axs[0].set_title(r"$\phi$-view")
axs[1].set_title(r"$\eta$-view")
axs[0].set_xlabel("x [cm]")
axs[0].set_ylabel("z [cm]")
axs[1].set_xlabel("x [cm]")

plt.tight_layout()
plt.show()
fig.savefig("./cms_dt_local_c.svg", dpi=dpi)
