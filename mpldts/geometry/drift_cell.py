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
from mpldts.geometry.transforms import TransformManager
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
    """

    def __init__(self, number=-1, parent=None):
        """
        Constructor for DriftCell.

        :param number: Identifier of the drift cell (default is -1).
        :type number: int, optional
        :param parent: Parent layer of the drift cell (default is None).
        :type parent: Layer, optional
        """
        # Parent rawId is used to get XML geometrical info to initialize
        # the instance. If not parent, attributes are set manually...
        self.parent = parent
        super().__init__()
        self.id = number
        self.number = number

        if parent:
            self.bounds = DTGEOMETRY.get("WiresSize", rawId=parent.id)
            self.local_center = DTGEOMETRY.get("LocalPosition", rawId=parent.id, w=number)
            self.global_center = DTGEOMETRY.get("GlobalPosition", rawId=parent.id, w=number)

        else:
            self.bounds = (4.2, 1.3, 235)
            self.local_center = (0, 0, 0)
            self.global_center = (0, 0, 0)

    def _setup_tranformer(self):
        """
        Set up the transformer for the Drift Cell. It defines the transformation from the local frame to the global frame.
        """
        from numpy import array

        self.transformer = TransformManager("Cell") # intial frame is the layer frame

        # Inherit transformation from the parent to the global frame
        if self.parent is not None:
            transform_matrix = self.parent.transformer.get_transformation("Station", "CMS")
            self.transformer.add("Station", "CMS", transformation_matrix=transform_matrix)
            transform_matrix = self.parent.transformer.get_transformation("SuperLayer", "Station")
            self.transformer.add("SuperLayer", "Station", transformation_matrix=transform_matrix)
            transform_matrix = self.parent.transformer.get_transformation("Layer", "SuperLayer")
            self.transformer.add("Layer", "SuperLayer", transformation_matrix=transform_matrix)

            # Define the transformation from the cell to the Layer frame
            _parent_center = self.parent.local_center
            _LTC = array([self._x_local, self._y_local, self._z_local]) - array(_parent_center) # This translation leave te cords in the SL frame

            self.transformer.add("Cell", "Layer", translation_vector=_LTC) # add the transformation from cell to Layer frame

if __name__ == "__main__":
    # This is to check that nothing fails
    dc = DriftCell(number=1)
    print(dc)
