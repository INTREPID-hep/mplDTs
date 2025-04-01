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

fig, ax = plt.subplots(1, 1, figsize=(14, 7), dpi=dpi)
axins = zoomed_inset_axes(ax, 4, loc='upper left', bbox_to_anchor=(1.1, 1.01), bbox_transform=ax.transAxes)

for sc in range(1, 15):
    for st in range(1, 5):
        if (sc == 13 or sc == 14) and st != 4:
            continue # Sector 13 and 14 are only one MB4 station
        station = Station(wheel=-2, sector=sc, station=st)
        _ = DTPatch(
            station,
            axes=ax,
            faceview="phi",
            local=False,
            bounds_kwargs=bounds_kwargs,
            cells_kwargs=cells_kwargs
        )

cells_kwargs["linewidth"] = .5 * 72 / dpi

for sc in [1, 2, 12]: # Only 3 sectors for the zoomed in view
    for st in range(1, 3):
        station = Station(wheel=-2, sector=sc, station=st)
        _ = DTPatch(
            station,
            axes=axins,
            faceview="phi",
            local=False,
            bounds_kwargs=bounds_kwargs,
            cells_kwargs=cells_kwargs
        )

ax.set_title("Global view of DT Stations on Wheel -2")
ax.set_xlabel("x [cm]")
ax.set_ylabel("y [cm]")

ax.set_xlim(-800, 800)
ax.set_ylim(-800, 800)

x1, x2, y1, y2 = 350, 550, -200, 200
axins.set_xlim(x1, x2)
axins.set_ylim(y1, y2)

plt.xticks(visible=False)
plt.yticks(visible=False)

mark_inset(ax, axins, loc1=2, loc2=3, fc="none", ec="0.5", edgecolor="r", color="red", fill=True)

plt.subplots_adjust(right=0.55)  # Increase space on the right

plt.show()
fig.savefig("cms_dts_phi_zoomed.svg", dpi=dpi)