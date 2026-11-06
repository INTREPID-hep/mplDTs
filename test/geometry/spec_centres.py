"""Cell centres derived from specs (test helper, not library code).

Composes station -> super layer -> layer -> cell poses. The runtime builder
(Phase 2) will own this logic; until then the oracle needs it here.
"""

from mpldts.geometry.specs import Pose


def cell_centres(station_spec):
    """{(sl, layer, cell): xyz} in the parent frame of the station."""
    centres = {}
    for super_layer in station_spec.super_layers:
        super_layer_frame = station_spec.pose.compose(super_layer.pose)
        for layer in super_layer.layers:
            layer_frame = super_layer_frame.compose(layer.pose)
            grid = layer.cells
            for x, number in zip(grid.x_positions(), grid.ids()):
                centre = layer_frame.compose(Pose.translated(x, 0.0, 0.0)).apply((0.0, 0.0, 0.0))
                centres[(super_layer.number, layer.number, number)] = centre
    return centres
