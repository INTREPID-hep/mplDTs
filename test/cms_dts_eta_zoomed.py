import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
from mpldts.geometry import Station
from mpldts.patches import DTPatch

dpi = 800

bounds_kwargs = {
    "linewidth": 72 / dpi,
    "edgecolor": "k",
    "facecolor": ["lightgray", "lightyellow", "lightpink", "lightblue"],
    "alpha": 0.4,
}
cells_kwargs = {
    "linewidth": .2 * 72 / dpi,
    "facecolor": "none",
    "edgecolor": "k",
}

fig, ax = plt.subplots(1, 1, figsize=(14, 5))
axins = zoomed_inset_axes(ax, 3, loc='upper left', bbox_to_anchor=(1.05, 1.1), bbox_transform=ax.transAxes)

for wh in range(-2, 3):
    for st in range(1, 5):
        station = Station(wheel=wh, sector=2, station=st)
        _ = DTPatch(
            station,
            axes=ax,
            faceview="eta",
            local=False,
            bounds_kwargs=bounds_kwargs,
            cells_kwargs=cells_kwargs
        )

cells_kwargs["linewidth"] = 0.5 * 72 / dpi

for wh in range(1, 3):
    for st in range(1, 3):
        station = Station(wheel=wh, sector=2, station=st)
        _ = DTPatch(
            station,
            axes=axins,
            faceview="eta",
            local=False,
            bounds_kwargs=bounds_kwargs,
            cells_kwargs=cells_kwargs
        )

ax.set_title("Global view of DT Stations on Sector 3")
ax.set_xlabel("z [cm]")
ax.set_ylabel("r [cm]")

ax.set_xlim(-800, 800)
ax.set_ylim(400, 800)

x1, x2, y1, y2 = 190, 610, 410, 540
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)

plt.xticks(visible=False)
plt.yticks(visible=False)

mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="0.5")

plt.subplots_adjust(right=0.55)  # Increase space on the right

plt.show()
fig.savefig("cms_dts_eta_zoomed.svg", dpi=500)