# Class definition of a Drift Cell.
#
# parent: layer in which the cell is ensembled
#
#           /                        /
#          /________________________/ 235 cm
#         |                         |
#         |                         |
#  1.3 cm |                         |
#         |                         | /
#         |_________________________|/
#         <------- 4.2 cm --------->


from mpldts.geometry import DTGEOMETRY, DTFrame


class DriftCell(DTFrame):
    """
    Class representing a Drift Cell.

    Attributes
    ----------
    driftTime : float
        Drift time of the drift cell.
    parent : Layer
        Parent layer of the drift cell.

    Others inherit from ``mpldts.geometry.DTFrame``... (e.g. local_center, global_center, direction, etc.)
    Bounds variables (width, height, length) are fixed values: 4.2 cm, 1.3 cm, 235 cm.
    """

    # class variables
    _height = float(DTGEOMETRY.root.find(".//Topology//cellHeight").text)
    _width = float(DTGEOMETRY.root.find(".//Topology//cellWidth").text)
    _length = float(DTGEOMETRY.root.find(".//Topology//cellLength").text)

    def __init__(self, number=-1, parent=None):
        """
        Constructor for DriftCell.

        :param number: Identifier of the drift cell (default is -1).
        :type number: int, optional
        :param parent: Parent layer of the drift cell (default is None).
        :type parent: Layer, optional
        """
        # Since it is initialized without rawId, no XML geometrical info will be used to initialize
        # the instance. Then, attributes is set manually...
        super().__init__()
        self.parent = parent
        self.id = number
        self.number = number
        self.local_center = self._compute_position("local")
        self.global_center = self._compute_position("global")
        self.direction = parent.direction if parent else (0, 0, 0)
        self._driftTime = 0

    # == Getters ==

    @property
    def driftTime(self):
        """
        Drift time of the drift cell.

        :return: Drift time.
        :rtype: float
        """
        return self._driftTime

    # == Setters ==

    @driftTime.setter
    def driftTime(self, time):
        """
        Set the drift time of the drift cell.

        :param time: Drift time.
        :type time: float
        """
        self._driftTime = time

    def _correct_cords(self, x, y, z):
        """
        Not correction needed since parent layer already applied the correction and set the local and global centers.

        :param x: x-coordinate.
        :type x: float
        :param y: y-coordinate.
        :type y: float
        :param z: z-coordinate.
        :type z: float
        :return: Corrected coordinates (x, y, z).
        :rtype: tuple
        """
        return x, y, z

    def _compute_position(self, position_type="local"):
        """
        Compute the position of the drift cell.

        :param position_type: Type of position to compute ("local" or "global").
        :type position_type: str
        :return: Position of the drift cell.
        :rtype: tuple
        """
        if self.parent:
            center = self.parent.local_center if position_type == "local" else self.parent.global_center
            x, y, z = center

            tag = "FirstWire_ref_to_chamber" if position_type == "local" else "FirstWire"
            first_wire_x = float(DTGEOMETRY.get(f".//WirePositions//{tag}", rawId=self.parent.id))

            cell_index = self.number - self.parent._first_cell_id
            x_cell = first_wire_x + cell_index * self._width if position_type == "local" else (x - first_wire_x) - cell_index * self._width
        else:
            x_cell, y, z = 0, 0, 0

        return x_cell, y, z
