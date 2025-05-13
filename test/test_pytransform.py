import matplotlib.pyplot as plt
import numpy as np
import pytransform3d.transformations as pt
from pytransform3d.rotations import norm_vector
from matplotlib.colors import Normalize
from mpldts.geometry import Station
from mpldts.patches import DTPatch
from matplotlib.transforms import Affine2D

cmap = plt.get_cmap("viridis")
cmap.set_under('none')
norm = Normalize(vmin=0.1, vmax=2, clip=False)

cell_kwargs = {
    "edgecolor": "black",
    "linewidth": 0.1,
    "cmap": cmap,
    "norm": norm
}


dt_info = [
    {"sl": 1, "l": 1, "w": 1, "time": 1, "time2": 5},
    {"sl": 1, "l": 2, "w": 1, "time": 1, "time2": 5},
    {"sl": 1, "l": 3, "w": 1, "time": 1, "time2": 5},
    {"sl": 1, "l": 4, "w": 2, "time": 1, "time2": 5},
    {"sl": 3, "l": 1, "w": 1, "time": 1, "time2": 5},
    {"sl": 3, "l": 2, "w": 1, "time": 1, "time2": 5},
    {"sl": 3, "l": 3, "w": 1, "time": 1, "time2": 5},
    {"sl": 3, "l": 4, "w": 2, "time": 1, "time2": 5}
]

chamber = Station(wheel=-1, sector=3, station=1, dt_info=dt_info)

fig, ax = plt.subplots(1, 1, figsize=(8, 5))

local_patch = DTPatch(
    chamber,
    axes=ax,
    faceview="phi",
    local=True,
    cells_kwargs=cell_kwargs,
)

global_patch = DTPatch(
    chamber,
    axes=ax,
    faceview="phi",
    local=False,
    cells_kwargs=cell_kwargs,
)

ax.set_xlim(-200, 500)
ax.set_ylim(-200, 200)

local_center_cell1 = chamber.super_layer(1).layer(1).cell(1).local_center
global_center_cell1 = chamber.super_layer(1).layer(1).cell(1).global_center

ax.scatter(
    local_center_cell1[0],
    local_center_cell1[2],
    marker="o",
    s=4,
    color="yellow",
)
ax.scatter(
    global_center_cell1[0],
    global_center_cell1[1],
    marker="o",
    s=4,
    color="red",

)

center_A = np.array([0, 0, 0])
center_B = np.array(chamber.global_center)
z_vector_B = np.array(chamber.direction)
z_vector_B = norm_vector(z_vector_B)
y_vector_B = np.array([0, 0, -1])
x_vector_B = np.cross(y_vector_B, z_vector_B)

R_AB = np.transpose(np.vstack((x_vector_B, y_vector_B, z_vector_B)))


translation_AB = center_B - center_A

T_AB = pt.transform_from(R_AB, translation_AB)

print("T_AB", T_AB)

# transform the point

P_A = np.array(local_center_cell1)
P_A_homogeneous = np.hstack((P_A, 1))#pt.to_homogeneous(P_A)

P_B_homogeneous = T_AB @ P_A_homogeneous

P_B = P_B_homogeneous[:3] / P_B_homogeneous[3]#pt.from_homogeneous(P_B_homogeneous)

print("P_B", P_B)
print("global_center_cell1", global_center_cell1)

ax.scatter(
    P_B[0],
    P_B[1],
    marker="o",
    s=5,
    color="k",
    alpha=0.5,
)

bounds_kwargs = {
    "linewidth": 0.3,
    "edgecolor": "r",
    # Fill colors for chamber, SL1, SL3, and SL2 in that order
    "facecolor": ["none", "none", "none", "none"],
}

local_patch_to_move = DTPatch(
    chamber,
    axes=ax,
    faceview="phi",
    local=True,
    vmap="time2",
    cells_kwargs=cell_kwargs,
    bounds_kwargs=bounds_kwargs,
)

affine_matrix_2d = np.array([
    [T_AB[0, 0], T_AB[0, 2], T_AB[0, 3]],
    [T_AB[1, 0], T_AB[1, 2], T_AB[1, 3]],
    [0,         0,         1]
])#np.vstack((T_AB[:2, :2], T_AB[:2, 3])).T
print("affine_matrix_2d", affine_matrix_2d)

trans = Affine2D(affine_matrix_2d)

local_patch_to_move.bounds_collection.set_transform(trans + ax.transData)
local_patch_to_move.cells_collection.set_transform(trans + ax.transData)

# ax.add_patch(local_patch_to_move)

# fig.savefig("test_pytransform.png", dpi=500)
plt.show()