from mpldts.geometry._geometry import DTGEOMETRY
from mpldts.geometry.dt_frame import DTFrame
from mpldts.geometry.super_layer import SuperLayer
from mpldts.geometry.transforms import TransformManager
from pandas import DataFrame
from copy import deepcopy
import warnings


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
                layer, and wire. e.g. ``[{"sl": 1, "l": 1, "w": 1, "time": 300}, ...]``
        :type dt_info: dict, list of dict, or pandas.DataFrame.
        """
        # == Chamber related parameters
        self.wheel = wheel
        self.sector = sector
        self.number = station
        self.id = DTGEOMETRY.get("rawId", wh=wheel, sec=sector, st=station)
        self.local_center = DTGEOMETRY.get("LocalPosition", rawId=self.id)
        self.global_center = DTGEOMETRY.get("GlobalPosition", rawId=self.id)
        self.direction = DTGEOMETRY.get("NormalVector", rawId=self.id)
        self.bounds = DTGEOMETRY.get("Bounds", rawId=self.id)
        self._setup_tranformer()

        # == Build the station
        self._super_layers = []
        self._build_station()

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

    def super_layer(self, super_layer_number):
        """
        Get a super layer by its number. if the super layer does not exist, it returns None.

        :param super_layer_number: Number of the super layer.
        :type super_layer_number: int
        :return: Super layer with the specified number.
        :rtype: SuperLayer
        """
        return next((sl for sl in self._super_layers if sl.number == super_layer_number), None)

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

    def _add_super_layer(self, super_layer):
        """
        Add a new super layer to the station.

        :param super_layer: Super layer to be added.
        :type super_layer: SuperLayer
        """
        self._super_layers.append(super_layer)

    def _build_station(self):
        """
        Build up the station. It creates the super layers contained in the station.
        """
        for SL in DTGEOMETRY.get(rawId=self.id).iter("SuperLayer"):
            self._add_super_layer(SuperLayer(rawId=SL.get("rawId"), parent=self))

    def _setup_tranformer(self):
        """
        Set up the transformer for the station. It defines the transformation from the local frame to the global frame.
        """
        from pytransform3d.rotations import perpendicular_to_vectors
        from numpy import array

        self.transformer = TransformManager("Station")  # intial frame is the station frame

        # negative wheel are facing towards the -z axis, positive wheel towards the +z axis, and 0 wheel is facing towards the +-z axis depending on the sector
        face_orientation = (
            -1
            if self._wheel < 0
            else 1 if self._wheel > 0 else -1 if self._sector in [1, 4, 5, 8, 9, 12, 13] else 1
        )

        # Define the transformation from Station frame to CMS global frame

        CMSezSt = self._direction
        CMSeySt = array([0, 0, 1]) * face_orientation
        CMSexSt = perpendicular_to_vectors(
            CMSeySt, CMSezSt
        )  # cross product to get the x axis of the local frame respect to the global frame

        _RCMSSt = array([CMSexSt, CMSeySt, CMSezSt]).T  # rotation matrix from local to global frame
        _TCMSSt = [
            self._x_global,
            self._y_global,
            self._z_global,
        ]  # translation vector from the DT center to the CMS center (0,0,0)

        self.transformer.add(
            "Station", "CMS", rotation_matrix=_RCMSSt, translation_vector=_TCMSSt
        )  # add the transformation from local to global frame

        # add a orientation transformation (Station 'Natural view' - NV phi/eta), useful for matplotlib ploting.
        StNvezSt = array([0, 0, -1])
        StNvPhieySt = array([0, -1, 0]) * face_orientation
        StNvPhiexSt = perpendicular_to_vectors(StNvPhieySt, StNvezSt)

        _RStNvPhiSt = array(
            [StNvPhiexSt, StNvPhieySt, StNvezSt]
        ).T  # rotation matrix from local to global frame

        self.transformer.add("Station", "StationNvPhi", rotation_matrix=_RStNvPhiSt)

        StNvEtaexSt = array([-1, 0, 0]) * face_orientation
        StNvEtaeySt = perpendicular_to_vectors(StNvezSt, StNvEtaexSt)

        _RStNvPhiSt = array(
            [StNvEtaexSt, StNvEtaeySt, StNvezSt]
        ).T  # rotation matrix from local to global frame

        self.transformer.add("Station", "StationNvEta", rotation_matrix=_RStNvPhiSt)

    def set_cell_attrs(self, dt_info):
        """
        Set the attributes for the drift cells in the station.

        :param dt_info: Drift cell information for the station. Can be a dictionary, a list of dictionaries,
                or a pandas DataFrame containing the drift cell attributes, they should be identified by super layer,
                layer, and wire. e.g. ``[{"sl": 1, "l": 1, "w": 1, "time": 300}, ...]``
        :type dt_info: dict, list, or pandas.DataFrame
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
                    "The drift cell information must contain the super layer, layer, and wire identifiers."
                )
            super_layer = self.super_layer(sl)

            if super_layer is None:
                warnings.warn(f"Super layer {sl} does not exist in station {self.name}.")
                continue

            cell = self.super_layer(sl).layer(l).cell(w)

            for key, value in info_item.items():
                setattr(cell, key, value)


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
