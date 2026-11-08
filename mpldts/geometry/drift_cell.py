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


from mpldts.geometry.dt_frame import DTFrame
from mpldts.geometry.frames import FrameView


class DriftCell(DTFrame):
    """
    Class representing a Drift Cell.

    Attributes
    ----------
        parent : Layer
            Parent layer of the drift cell.
        id : int
            Identifier of the drift cell.
        number : int
            Number of the drift cell. Same as id.

        Others inherit from ``mpldts.geometry.DTFrame``... (e.g. local_center, direction, etc.)
    """

    def __init__(self, number=-1, parent=None):
        """
        Constructor for DriftCell.

        :param number: Identifier of the drift cell (default is -1).
        :type number: int, optional
        :param parent: Parent layer of the drift cell.
        :type parent: Layer
        """
        self.parent = parent
        self.id = number
        self.number = number

        if parent is None:
            raise ValueError("DriftCell needs its layer (Station.from_spec).")

        node = parent._cells.get("C%d" % number)
        if node is None:
            raise ValueError(f"cell {number} is not in layer {parent.number}")
        width, length, thickness = node.shape.aabb()
        self.bounds = (width, thickness, length)
        self.local_center = parent._cell_local[number]
        self.global_center = tuple(float(value) for value in node.world_pose.translation)
        self._node = node
        self.transformer = FrameView(parent.transformer.graph, node)
