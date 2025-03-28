import matplotlib.pyplot as plt
from mpldts.geometry import Station
from mpldts.patches import DTPatch

dpi = 100  # Plot resolution

# Cell appearance configuration
cells_kwargs = {
    "linewidth": .4 * 72 / dpi,
    "facecolor": "none",
    "edgecolor": "k",
}

# Create figure and subplots
fig, axs = plt.subplots(1, 2, figsize=(15, 7), sharey=True, dpi=dpi)
axs = axs.flatten()

# Define DT station
station = Station(wheel=-1, sector=1, station=2)

# Create patches for phi-view and eta-view
dt_patch_phi = DTPatch(
    station, axes=axs[0], faceview="phi", local=True, cells_kwargs=cells_kwargs
)
dt_patch_z = DTPatch(
    station, axes=axs[1], faceview="eta", local=True, cells_kwargs=cells_kwargs
)

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
fig.savefig("./cms_dt_local_wb.svg", dpi=dpi)
