"""Legacy CMS station wrapper (T-022).

A Station is a view over the T-011 source and the T-020 node tree:

    CMSXMLSource.record()   ids, local positions and bounds, verbatim XML
    CMSXMLSource.station()  StationSpec
    build_station()         node tree with parent-relative poses
    FrameGraph / FrameView  every frame, including the plotting ones

The data attributes keep the XML values (conventions section 7.3): the frame
chain never reads them, it is the node poses. That is what removes BUG-01.
"""

from copy import deepcopy
import threading
import warnings
from typing import Any, Optional

import numpy as np
from pandas import DataFrame

from mpldts.geometry.dt_frame import DTFrame
from mpldts.geometry.frames import FrameGraph, FrameView
from mpldts.geometry.model import build_station
from mpldts.geometry.sources.cms_xml import CMSXMLSource
from mpldts.geometry.specs import Pose
from mpldts.geometry.super_layer import SuperLayer

_SOURCE = None


def _source():
    """The CMS XML source of the package geometry, parsed once."""
    global _SOURCE
    if _SOURCE is None:
        _SOURCE = CMSXMLSource()
    return _SOURCE


def station_for(raw_id):
    """The Station holding the XML element with this rawId (legacy constructors)."""
    try:
        key = _source().chamber_of(raw_id)
    except KeyError:
        raise ValueError("rawId %r is not a CMS geometry element" % (raw_id,)) from None
    return Station(*key)


def _unit(vector):
    return vector / np.linalg.norm(vector)


class Station(DTFrame):
    """
    Class representing a CMS Drift Tube Chamber.

    Attributes
    ----------
        wheel : int
            Geometrical position within CMS.
        sector : int
            Geometrical position within CMS.
        number : int
            Station type (1: MB1, 2: MB2, 3: MB3, or 4: MB4).
        name : str
            Name of the station. Returns "Wheel {wheel}, Sector {sector}, Station {number}".
        super_layers : list
            List of super layers in the station.

        Others inherit from ``mpldts.geometry.DTFrame``... (e.g. id, local_center, global_center, direction, etc.)
    """

    def __init__(self, wheel, sector, station, dt_info=None):
        """
        Constructor of the Station class.

        :param wheel: Wheel position within CMS.
        :type wheel: int
        :param sector: Sector position within CMS.
        :type sector: int
        :param station: Station type (1: MB1, 2: MB2, 3: MB3, or 4: MB4).
        :type station: int
        :param dt_info: Information for the station at cell level. Default is None. Drift cell information for the station. Can be a dictionary, a list of dictionaries,
                or a pandas DataFrame containing the drift cell attributes, they should be identified by super layer,
                layer, and cell. e.g. `[{"sl": 1, "l": 1, "w": 1, "time": 300}, ...]`
        :type dt_info: dict, list of dict, or pandas.DataFrame.
        """
        # == Chamber related parameters
        self.wheel = wheel
        self.sector = sector
        self.number = station

        source = _source()
        try:
            record = source.record(wheel, sector, station)
            spec = source.station(wheel, sector, station)
        except KeyError:
            raise ValueError(
                "chamber Wh:%d St:%d Se:%d is not in the CMS geometry" % (wheel, station, sector)
            ) from None

        self.id = record["id"]
        self.local_center = record["local"]
        self.global_center = record["global"]
        self.direction = record["direction"]
        self.bounds = record["bounds"]

        # == Build the station: node tree, one graph, one view per object
        self._node = build_station(spec)
        self._graph = FrameGraph()
        self._graph.add_nodes(self._node)
        self.transformer = FrameView(self._graph, self._node)

        # rawId -> (node, record), for the legacy child constructors
        self._parts = {}
        for sl_record, sl_node in zip(record["super_layers"], self._node.children):
            self._parts[sl_record["raw_id"]] = (sl_node, sl_record)
            for layer_record, layer_node in zip(sl_record["layers"], sl_node.children):
                self._parts[layer_record["raw_id"]] = (layer_node, layer_record)

        self._super_layers = [
            SuperLayer(rawId=sl_record["raw_id"], parent=self)
            for sl_record in record["super_layers"]
        ]
        self._add_plotting_frames()

        # == Set the drift cell attributes
        if dt_info is not None:
            self.set_cell_attrs(dt_info)

    # == Getters

    @property
    def wheel(self):
        """
        Wheel position within CMS.

        :return: Wheel position.
        :rtype: int
        """
        return self._wheel

    @property
    def sector(self):
        """
        Sector position within CMS.

        :return: Sector position.
        :rtype: int
        """
        return self._sector

    @property
    def name(self):
        """
        Name of the station.

        :return: Name of the station in format "Wheel {wheel}, Sector {sector}, Station {number}".
        :rtype: str
        """
        return f"Wheel {self._wheel}, Sector {self._sector}, Station {self._number}"

    @property
    def super_layers(self):
        """
        Get all the super layers in the station.

        :return: List of super layers in the station.
        :rtype: list
        """
        return self._super_layers

    @property
    def face_orientation_factor(self):
        """
        Get the face orientation factor of the station. It is -1 for negative wheels, 1 for positive
        wheels, and it depends on the sector for wheel 0 (it is -1 for sectors 1, 4, 5, 8, 9, 12,
        and 13, and 1 otherwise). Details in https://dt-sx5.web.cern.ch/dt-sx5/run/docs/050912DT_type_naming.pdf

        :return: Face orientation factor.
        :rtype: int
        """
        return (
            -1
            if self._wheel < 0
            else 1 if self._wheel > 0 else -1 if self._sector in [1, 4, 5, 8, 9, 12, 13] else 1
        )

    def super_layer(self, super_layer_number):
        """
        Get a super layer by its number. if the super layer does not exist, it returns None.

        :param super_layer_number: Number of the super layer.
        :type super_layer_number: int
        :return: Super layer with the specified number.
        :rtype: SuperLayer
        """
        return next((sl for sl in self._super_layers if sl.number == super_layer_number), None)

    def _legacy_part(self, raw_id):
        """(node, record) of a super layer or layer of this station, by rawId."""
        try:
            return self._parts[int(raw_id)]
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                "rawId %r is not a super layer or layer of station %s" % (raw_id, self.name)
            ) from None

    # == Setters

    @wheel.setter
    def wheel(self, value):
        """
        Set the wheel position.

        :param value: Wheel position.
        :type value: int
        :raises ValueError: If the value is not between -2 and 2.
        """
        if value < -2 or value > 2:
            raise ValueError("Wheel value must be between -2 and 2")
        self._wheel = value

    @sector.setter
    def sector(self, value):
        """
        Set the sector position.

        :param value: Sector position.
        :type value: int
        :raises ValueError: If the value is not between 1 and 14.
        """
        if value < 1 or value > 14:
            raise ValueError("Sector value must be between 1 and 14")
        else:
            self._sector = value

    @DTFrame.number.setter
    def number(self, value):
        """
        Set the station type.

        :param value: Station type.
        :type value: int
        :raises ValueError: If the value is not between 1 and 4.
        """
        if value < 1 or value > 4:
            raise ValueError("Station value must be between 1 and 4")
        self._number = value

    # == Frames for the plotting patches

    def _add_plotting_frames(self):
        """
        Register the frames the plotting patches ask for: the natural views
        StationNvPhi and StationNvEta, the sector phi line (SectorRef) and the
        geometrical center of the super layers 1 and 3 (SL13Center).
        """
        station_frame = self._node.frame_id

        def add(name, pose):
            self._graph.add_virtual(station_frame + "/" + name, station_frame, pose)

        face = self.face_orientation_factor

        # Station 'Natural view' (phi): a rotation, the station frame to the view frame
        ez = np.array([0.0, 0.0, -1.0])
        ey = np.array([0.0, -1.0, 0.0]) * face
        ex = _unit(np.cross(ey, ez))
        add("StationNvPhi", Pose(np.column_stack([ex, ey, ez]).T))

        # Station 'Natural view' (eta)
        ex = np.array([-1.0, 0.0, 0.0]) * face
        ey = _unit(np.cross(ez, ex))
        add("StationNvEta", Pose(np.column_stack([ex, ey, ez]).T))

        # Sector phi line (AM trigger primitives). MB4 sectors 4 and 10 are
        # divided into 13 and 14, hence the sign correction.
        x, y, _ = self.global_center
        sector = self._sector
        correction = 1
        if sector in [13, 14]:
            correction = -1
            sector = 4 if sector == 13 else 10
        dphi = np.arctan2(y, x) - (sector - 1) * np.pi / 6 * correction
        dx = -np.sin(dphi) * np.hypot(x, y) * face * correction
        add("SectorRef", Pose.translated(-dx, 0.0, 0.0))

        # Geometrical center of the super layers 1 and 3
        sl1 = self.super_layer(1)
        sl3 = self.super_layer(3)
        if sl1 is not None and sl3 is not None:
            centre = (np.asarray(sl1.local_center) + np.asarray(sl3.local_center)) / 2.0
            add("SL13Center", Pose.translated(*centre))

    def set_cell_attrs(self, dt_info):
        """
        Set the attributes for the drift cells in the station.

        :param dt_info: Drift cell information for the station. Can be a dictionary, a list of dictionaries,
                or a pandas DataFrame containing the drift cell attributes, they should be identified by super layer,
                layer, and cell. e.g. `[{"sl": 1, "l": 1, "w": 1, "time": 300}, ...]`
        :type dt_info: dict, list, or pandas.DataFrame

        .. note::
            This writes on this station's own cells. On a station shared through
            :class:`StationsCache` use :meth:`overlay` instead: the cache hands
            the same instance to every caller.
        """
        if isinstance(dt_info, dict):
            info = [deepcopy(dt_info)]
        elif isinstance(dt_info, DataFrame):
            info = dt_info.to_dict(orient="records")
        elif isinstance(dt_info, list):
            info = deepcopy(dt_info)
        else:
            raise TypeError(
                "The drift time information must be a dictionary, a list of dictionaries, or a pandas DataFrame."
            )

        for info_item in info:
            sl = info_item.pop("sl", None)
            l = info_item.pop("l", None)
            w = info_item.pop("w", None)
            if not all([sl, l, w]):
                raise ValueError(
                    "The drift cell information must contain the super layer, layer, and cell identifiers."
                )
            super_layer = self.super_layer(sl)

            if super_layer is None:
                warnings.warn(f"Super layer {sl} does not exist in station {self.name}.")
                continue

            cell = self.super_layer(sl).layer(l).cell(w)

            for key, value in info_item.items():
                setattr(cell, key, value)

    def overlay(self, dt_info=None):
        """
        A per-event view of this station: the same geometry, its own cell attributes.

        The node tree and the frame graph are shared with this station, so an
        overlay costs a fraction of a full build; the super layers, layers and
        cells are new objects, so setting an attribute on an overlay cell never
        reaches the station or another overlay.

        :param dt_info: Drift cell information, as in :meth:`set_cell_attrs`.
        :type dt_info: dict, list of dict, or pandas.DataFrame, optional
        :return: The overlay station.
        :rtype: Station
        """
        view = object.__new__(type(self))
        view.__dict__.update(self.__dict__)
        view.transformer = FrameView(self._graph, self._node)
        view._super_layers = [SuperLayer(rawId=sl.id, parent=view) for sl in self._super_layers]
        if dt_info is not None:
            view.set_cell_attrs(dt_info)
        return view


if __name__ == "__main__":
    # This is to check that nothing fails
    st = Station(
        wheel=-2,
        sector=1,
        station=2,
        dt_info=[
            {"sl": 1, "l": 1, "w": 10, "time": 10, "size": 2, "other": 34},
            {"sl": 1, "l": 2, "w": 10, "time": 10, "size": 2, "other": 34},
            {"sl": 1, "l": 3, "w": 10, "time": 10, "size": 2, "other": 34},
            {"sl": 1, "l": 4, "w": 20, "time": 10, "size": 2, "other": 34},
            {"sl": 3, "l": 1, "w": 10, "time": 10, "size": 2, "other": 34},
            {"sl": 3, "l": 2, "w": 10, "time": 10, "size": 2, "other": 34},
            {"sl": 3, "l": 3, "w": 10, "time": 10, "size": 2, "other": 34},
            {"sl": 3, "l": 4, "w": 20, "time": 10, "size": 2, "other": 34},
        ],
    )
    print(st)
    for sl in st.super_layers:
        print("\t", sl)
        for l in sl.layers:
            print(2 * "\t", l)
            print(3 * "\t", l.cell(l._first_cell_id))
            print(3 * "\t", l.cell(len(l.cells) - 1))
    print(
        "\t",
        f"properties contained into cells: {st.super_layer(1).layer(1).cells[0].__dict__.keys()}",
    )


class StationsCache:
    """Singleton cache for Station objects to avoid recreating expensive geometry."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._cache_lock = threading.Lock()
        return cls._instance

    def get(self, wh: int, sc: int, st: int, dt_info: Optional[Any] = None) -> Optional[Station]:
        """The cached station of a chamber, or a per-event overlay of it.

        The cached station is never mutated: when `dt_info` is given the
        result is :meth:`Station.overlay`, which shares the geometry and owns
        its cell attributes.
        """
        key = (wh, sc, st)
        with self._cache_lock:
            station = self._cache.get(key)
            if station is None:
                try:
                    station = Station(wheel=wh, sector=sc, station=st)
                    self._cache[key] = station
                except ValueError:
                    self._cache[key] = None
                    return None
            if dt_info is None:
                return station
            return station.overlay(dt_info)
    
    def clear(self):
        """Clear the cache (useful for testing or memory management)."""
        with self._cache_lock:
            self._cache.clear()
    
    def size(self):
        """Return the number of cached stations."""
        with self._cache_lock:
            return len(self._cache)

STATION_CACHE = StationsCache()
