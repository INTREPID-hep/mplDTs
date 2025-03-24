from mpldts.geometry import Station
from mpldts.patches import DTPatch
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt

cmap = plt.get_cmap('viridis').copy()
cmap.set_under('none')
norm = Normalize(vmin=9, vmax=100)

def main_global(faceview="phi"):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    for sc in range(1, 15):
        for st in range(1, 5):
            if (sc == 13 or sc == 14) and st != 4:
                continue 
            station = Station(wheel=-2, sector=sc, station=st, dt_info=[
                        {"sl": 1, "l": 1, "w": 1, "time": 10},
                        {"sl": 1, "l": 2, "w": 1, "time": 10},
                        {"sl": 1, "l": 3, "w": 1, "time": 10},
                        {"sl": 1, "l": 4, "w": 2, "time": 10},
                        {"sl": 3, "l": 1, "w": 1, "time": 10},
                        {"sl": 3, "l": 2, "w": 1, "time": 10},
                        {"sl": 3, "l": 3, "w": 1, "time": 10},
                        {"sl": 3, "l": 4, "w": 2, "time": 10},
                    ])
            _ = DTPatch(station, axes=ax, faceview=faceview, local=False, bounds_kwargs={"linewidth": 0.1, "facecolor": "none"}, cells_kwargs={"linewidth": 0.05, "edgecolor": "k", "cmap": cmap, "norm": norm})

    circle = plt.Circle((0, 0), 800, color="gray", alpha=0.05, edgecolor="none")
    ax.add_patch(circle)
    ax.set_title("Global view of DT Stations")
    ax.set_xlabel("x [cm]")
    ax.set_ylabel("-z [cm]")

    ax.set_xlim(-800, 800)
    ax.set_ylim(-800, 800)

    plt.show()

def main_local(faceview="phi"):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    station = Station(wheel=-2, sector=1, station=1,
                    dt_info=[
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
                        {"sl": 3, "l": 4, "w": 2, "time": 10},
                    ])
    _ = DTPatch(station, axes=ax, faceview=faceview, local=True, cells_kwargs={"edgecolor": "k", "cmap": cmap, "norm": norm})

    width, height, length = station.bounds
    x, y, _ = station.local_center
    if faceview == "phi":
        ax.set_xlim(x - width / 2, x + width / 2)
    else:
        ax.set_xlim(x - length / 2, x + length / 2)

    ax.set_ylim(y - height / 2, y + height / 2)
    ax.set_xlabel("x [cm]")
    ax.set_ylabel("-z [cm]")
    ax.set_title(f"Local view of a DT Station : {station.name}")

    plt.show()

if __name__ == "__main__":
    main_local(faceview="z")
    # main_global()