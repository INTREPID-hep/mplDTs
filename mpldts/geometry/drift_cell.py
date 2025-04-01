# Class definition of a Drift Cell.
#
# parent: layer in which the cell is ensembled
#
#           /                        /
#          /________________________/ 235 cm
#         |                         |
#         |                         |
#  1.3 cm |            o            |
#         |                         | /
#         |_________________________|/
#         <------- 4.2 cm --------->


from mpldts.geometry._geometry import DTGEOMETRY
from mpldts.geometry.dt_frame import DTFrame
import warnings as Warning


class DriftCell(DTFrame):
    """
    Class representing a Drift Cell.

    Attributes
    ----------
        parent : Layer
            Parent layer of the drift cell.

        Others inherit from ``mpldts.geometry.DTFrame``... (e.g. local_center, direction, etc.)
        Bounds variables (width, height, length) are fixed values: 4.2 cm, 1.3 cm, 235 cm (aprox).

    .. note::
        - The `global_center` property is not implemented yet
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
        # Since rawId is not provided, no XML geometrical info will be used to initialize
        # the instance. Then, attributes are set manually...
        super().__init__()
        self.parent = parent
        self.id = number
        self.number = number
        self.local_center = self._compute_position()

    # == Getters ==

    @DTFrame.global_center.getter
    def global_center(self):
        """
        Global position of the drift cell.

        .. warning::
            This property is not implemented yet.

        :return: Global position of the drift cell.
        :rtype: tuple
        """
        Warning.warn("Global position is not implemented yet for Drift Cells.")
        return None

    # == Setters ==

    def _compute_position(self):
        """
        Compute the position of the drift cell.

        :return: Position of the drift cell.
        :rtype: tuple
        """
        if self.parent:
            center = self.parent.local_center
            x, y, z = center

            first_wire_x = float(
                DTGEOMETRY.get(f".//WirePositions//FirstWire_ref_to_chamber", rawId=self.parent.id)
            )

            cell_index = self.number - self.parent._first_cell_id
            x_cell = first_wire_x + cell_index * self._width
        else:
            x_cell, y, z = 0, 0, 0

        return x_cell, y, z


if __name__ == "__main__":
    # This is to check that nothing fails
    dc = DriftCell(number=1)
    print(dc)
