"""Short constructors for hand-written specs (T-050).

The spec dataclasses are explicit on purpose, but writing a small test beam
station by hand should not need six keyword arguments per layer. These four
builders fill the defaults (identity pose, no envelope, air in the chamber,
vacuum in the world) and leave everything else to the dataclass.

    layer = make_layer(1, CellGrid(pitch=4.2, count=24, shape=Box(4.2, 120.0, 1.3),
                                   material="GasMixture"))
    station = make_station("TB-1", [make_superlayer(1, [layer])],
                           shape=Box(110.0, 130.0, 40.0))

Nothing here validates eagerly: `validate()` stays the single gate, so a spec built
with these helpers fails exactly where a spec built by hand does.
"""

from __future__ import annotations

from mpldts.geometry.specs import (
    DetectorSpec,
    LayerSpec,
    Pose,
    StationSpec,
    SuperLayerSpec,
)

__all__ = ["make_layer", "make_superlayer", "make_station", "make_detector"]


def make_layer(number, cells, pose=None, shape=None, material=None):
    """One layer: a cell grid and, optionally, its envelope."""
    return LayerSpec(
        number=number,
        pose=Pose.identity() if pose is None else pose,
        cells=cells,
        shape=shape,
        material=material,
    )


def make_superlayer(number, layers, pose=None, shape=None, material=None):
    """One super layer: its layers and, optionally, its envelope."""
    return SuperLayerSpec(
        number=number,
        pose=Pose.identity() if pose is None else pose,
        layers=list(layers),
        shape=shape,
        material=material,
    )


def make_station(name, super_layers, pose=None, shape=None, material="G4_AIR", attachments=()):
    """One chamber: its super layers, an optional envelope and its panels."""
    return StationSpec(
        name=name,
        pose=Pose.identity() if pose is None else pose,
        super_layers=list(super_layers),
        shape=shape,
        material=material,
        attachments=list(attachments),
    )


def make_detector(name, stations, pose=None, shape=None, material="G4_Galactic", structure=()):
    """The assembly: the stations of the detector and the world frame."""
    return DetectorSpec(
        name=name,
        pose=Pose.identity() if pose is None else pose,
        stations=list(stations),
        shape=shape,
        material=material,
        structure=list(structure),
    )
