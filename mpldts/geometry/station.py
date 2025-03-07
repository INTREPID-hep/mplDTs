from mpldts.geometry import DTGEOMETRY, DTFrame
from mpldts.geometry.super_layer import SuperLayer
from pandas import DataFrame


class Station(DTFrame):
    """
    Class representing a CMS Drift Tube Chamber.

    Attributes
    ----------
    wheel : int
        Geometrical position within CMS.
    sector : int
        Geometrical position within CMS.
    station : int
        Geometrical position within CMS.
    name : str
        Name of the station. returns "Wheel {wheel}, Sector {sector}, Station {station}".
    super_layers : list
        List of super layers in the station.

    Others inherit from ``mpldt.geometry.DTFrame``... (e.g. id, local_center, global_center, direction, etc.)
    """

    def __init__(self, wheel, sector, station, dt_info=None):
        """
        Constructor of the Station class.

        :param wheel: Wheel position within CMS.
        :type wheel: int
        :param sector: Sector position within CMS.
        :type sector: int
        :param station: Station type.
        :type station: int
        :param dt_info: Drift time information for the station. Default is None.
        :type dt_info: dict, list, or pandas.DataFrame
        """
        super().__init__(
            rawId=DTGEOMETRY.get("rawId", wh=wheel, sec=sector, st=station)
        )
        self.number = None

        # == Chamber related parameters
        self.wheel = wheel
        self.sector = sector
        self.station = station

        # == Build the station
        self._super_layers = []
        self._build_station()

        # == Set the drift times
        if dt_info is not None:
            self.set_cell_times(dt_info)

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
    def station(self):
        """
        Station type.

        :return: Station position.
        :rtype: int
        """
        return self._station

    @property
    def name(self):
        """
        Name of the station.

        :return: Name of the station in format "Wheel {wheel}, Sector {sector}, Station {station}".
        :rtype: str
        """
        return f"Wheel {self.wheel}, Sector {self.sector}, Station {self.station}"

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
        return next(
            (sl for sl in self.super_layers if sl.number == super_layer_number), None
        )

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

    @station.setter
    def station(self, value):
        """
        Set the station type.

        :param value: Station type.
        :type value: int
        :raises ValueError: If the value is not between 1 and 4.
        """
        if value < 1 or value > 4:
            raise ValueError("Station value must be between 1 and 4")
        self._station = value

    def _add_super_layer(self, super_layer):
        """
        Add a new super layer to the station.

        :param super_layer: Super layer to be added.
        :type super_layer: SuperLayer
        """
        self.super_layers.append(super_layer)

    def _correct_cords(self, x, y, z):
        """
        Correct the coordinates of the station. Bear in mind that the station reference
        frame is rotated pi/2 with respect to the CMS frame along x direction:

        CMS -> x: right, y: up, z: forward, Station -> x: right, y: forward, z: down

        That is, a rotation matrix of -90 degrees around the x-axis.

        .. math::

            R_x(-\\pi/2) = \\begin{bmatrix} 
                                1 & 0 & 0 \\\\
                                0 & 0 & 1 \\\\
                                0 & -1 & 0
                            \\end{bmatrix}

        :param x: x coordinate.
        :type x: float
        :param y: y coordinate.
        :type y: float
        :param z: z coordinate.
        :type z: float
        :return: Transformed coordinates.
        :rtype: tuple
        """
        return x, z, -1 * y

    def _build_station(self):
        """
        Build up the station. It creates the super layers contained in the station.
        """
        for SL in DTGEOMETRY.get(rawId=self.id).iter("SuperLayer"):
            new_super_layer = SuperLayer(rawId=SL.get("rawId"), parent=self)
            self._add_super_layer(new_super_layer)

    def set_cell_times(self, dt_info):
        """
        Set the drift times for the cells in the station.

        :param dt_info: Drift time information for the station. Can be a dictionary, a list of dictionaries,
                or a pandas DataFrame containing the drift time information identified by super layer,
                layer, and wire. e.g. [{"sl": 1, "l": 1, "w": 1, "time": 300}, ...]
        :type dt_info: dict, list, or pandas.DataFrame
        """
        info_iter = (
            DataFrame(dt_info) if isinstance(dt_info, (dict, list)) else dt_info
        ).itertuples(index=False)
        for info in info_iter:
            sl, l, w, time = info.sl, info.l, info.w, info.time
            try:
                self.super_layer(sl).layer(l).cell(w).driftTime = time
            except:
                pass


if __name__ == "__main__":
    local = False
    st = Station(wheel=-2, sector=1, station=4)
    print("Local: ", local)
    print("Station center:", st.local_center if local else st.global_center)
    print("Station direction:", st.direction)
    for sl in st.super_layers:
        print(
            f">Super Layer {sl.number} center:",
            sl.local_center if local else sl.global_center,
        )
        for l in sl.layers:
            print(
                f"->Layer {l.number} center:",
                l.local_center if local else l.global_center,
            )
            print(
                f"---First Cell center:",
                l.cells[0].local_center if local else l.cells[0].global_center,
            )
            print(
                f"---Last Cell center:",
                l.cells[-1].local_center if local else l.cells[-1].global_center,
            )
