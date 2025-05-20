import matplotlib.pyplot as plt
from mpldts.geometry import Station
from mpldts.patches import DTStationPatch

# make a illustration of the eta of the stations and the first cell of super layer 2
dpi = 800

bounds_kwargs = {
    "linewidth": 72 / dpi,
    "edgecolor": "k",
    "facecolor": ["lightgray", "lightyellow", "lightpink", "lightblue"],
    "alpha": 0.4,
}
cells_kwargs = {
    "linewidth": 0.2 * 72 / dpi,
    "facecolor": "none",
    "edgecolor": "k",
}

fig, ax = plt.subplots(1, 1, figsize=(12, 5))

stations = [
    {"wheel": -2, "sector": 2, "station": 2},
    {"wheel": -1, "sector": 2, "station": 1},
    {"wheel": 0, "sector": 2, "station": 3},
    {"wheel": 1, "sector": 2, "station": 2},
    {"wheel": 2, "sector": 2, "station": 1},
]

for station_info in stations:
    wh, sc, st = station_info["wheel"], station_info["sector"], station_info["station"]
    station = Station(wheel=wh, sector=sc, station=st)
    _ = DTStationPatch(
        station,
        axes=ax,
        faceview="eta",
        local=False,
        bounds_kwargs=bounds_kwargs,
        cells_kwargs=cells_kwargs,
    )

    global_center = station.global_center
    (
        _,
        height,
        length,
    ) = station.bounds
    # Draw vector from origin to station global center
    z, r = global_center[2], (global_center[0] ** 2 + global_center[1] ** 2) ** 0.5
    ax.text(z - length / 2, r + height + 0.2, f"{station.name}", color="black", fontsize=6)
    ax.scatter(z, r, marker="o", color="blue", s=0.08)
    ax.arrow(
        0,
        0,
        z,
        r,
        length_includes_head=True,
        head_width=0.01,
        head_length=0.01,
        linewidth=0.1,
        color="blue",
        hatch="X",
    )
    ax.text(z + 2, r, r"$\eta$" + f": {station.eta:.2f}", color="blue", fontsize=5)

    # Draw vector from origin to first cell of super layer 2
    first_cell = station.super_layer(2).layer(1).cells[0]
    first_cell_position = first_cell.global_center
    z_cell, r_cell = (
        first_cell_position[2],
        (first_cell_position[0] ** 2 + first_cell_position[1] ** 2) ** 0.5,
    )
    ax.scatter(z_cell, r_cell, marker="o", color="red", s=0.08)
    ax.arrow(
        0,
        0,
        z_cell,
        r_cell,
        length_includes_head=True,
        head_width=0.01,
        head_length=0.01,
        linewidth=0.1,
        color="red",
        hatch="X",
    )
    ax.text(z_cell + 2, r_cell, r"$\eta$" + f": {first_cell.eta:.2f}", color="red", fontsize=5)


ax.set_title(r"$\eta$ of Station and first cell of SL2 centers")
ax.set_xlabel("z [cm]")
ax.set_ylabel("r [cm]")

ax.set_xlim(-800, 800)
ax.set_ylim(0, 800)

fig.savefig("cms_dts_etas.svg", dpi=500)
