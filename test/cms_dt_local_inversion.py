import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpldts.geometry import Station
from mpldts.patches import DTPatch

cmap = plt.get_cmap('viridis').copy()
cmap.set_under('none')
norm = Normalize(vmin=0.1, vmax=20)

dpi=100

bounds_kwargs = {
    "linewidth": 72 / dpi,
    "edgecolor": "k",
    "facecolor": ["lightgray", "lightyellow", "lightpink", "lightblue"],
    "alpha": 0.3,
}
cells_kwargs = {
    "linewidth": .4 * 72 / dpi,
    "edgecolor": "k",
    "cmap": cmap,
    "norm": norm,
}

dt_info = [
    {"sl": 1, "l": 1, "w": 1, "time": 10},
    {"sl": 1, "l": 2, "w": 1, "time": 10},
    {"sl": 1, "l": 3, "w": 1, "time": 10},
    {"sl": 1, "l": 4, "w": 2, "time": 10},
    {"sl": 2, "l": 1, "w": 1, "time": 10},
    {"sl": 2, "l": 2, "w": 1, "time": 10},
    {"sl": 2, "l": 3, "w": 1, "time": 10},
    {"sl": 2, "l": 4, "w": 2, "time": 10},
    {"sl": 3, "l": 1, "w": 1, "time": 10},
    {"sl": 3, "l": 2, "w": 1, "time": 10},
    {"sl": 3, "l": 3, "w": 1, "time": 10},
    {"sl": 3, "l": 4, "w": 2, "time": 10}
]

fig, axs = plt.subplots(2, 2, figsize=(10, 10), dpi=dpi)
axs = axs.flatten()

station = Station(wheel=-1, sector=1, station=2, dt_info=dt_info)

dt_patch_phi = DTPatch(station, axes=axs[0], faceview="phi", local=True, cells_kwargs=cells_kwargs, bounds_kwargs=bounds_kwargs)
dt_patch_z = DTPatch(station, axes=axs[2], faceview="eta", local=True, cells_kwargs=cells_kwargs, bounds_kwargs=bounds_kwargs)
dt_patch_phi = DTPatch(station, axes=axs[1], faceview="phi", local=True, inverted=True, cells_kwargs=cells_kwargs, bounds_kwargs=bounds_kwargs)
dt_patch_z = DTPatch(station, axes=axs[3], faceview="eta", local=True, inverted=True, cells_kwargs=cells_kwargs, bounds_kwargs=bounds_kwargs)

line = plt.Line2D((.5,.5),(.1,.9), color="k", linewidth=2)
fig.add_artist(line)

width, height, length = station.bounds
x, y, z = station.local_center

axs[0].set_xlim(x - width / 2 - 5, x + width / 2 + 5)
axs[0].set_ylim(z - height / 2 - 5, z + height / 2 + 5)

axs[2].set_xlim(y - length / 2 - 5, y + length / 2 + 5)
axs[2].set_ylim(z - height / 2 - 5, z + height / 2 + 5)

axs[1].set_xlim(x - width / 2 - 5, x + width / 2 + 5)
axs[1].set_ylim(z - height / 2 - 5, z + height / 2 + 5)

axs[3].set_xlim(y - length / 2 - 5, y + length / 2 + 5)
axs[3].set_ylim(z - height / 2 - 5, z + height / 2 + 5)

fig.suptitle(f"Local view of a DT Station : {station.name}")

axs[0].set_xlabel("x [cm]")
axs[0].set_ylabel("z [cm]")
axs[0].set_title(r"$\phi$-view")	

axs[2].set_xlabel("x [cm]")
axs[2].set_ylabel("z [cm]")
axs[2].set_title(r"$\eta$-view")

axs[1].set_xlabel("x [cm]")
axs[1].set_ylabel("-z [cm]")
axs[1].set_title(r"$\phi$-view (inverted)")

axs[3].set_xlabel("-x [cm]")
axs[3].set_ylabel("-z [cm]")
axs[3].set_title(r"$\eta$-view (inverted)")

plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.4, hspace=0.4)
plt.show()
fig.savefig("./cms_dt_local_inversion.svg", dpi=dpi)