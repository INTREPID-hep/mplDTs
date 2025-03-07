from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from mpldts.geometry.station import Station
from mpldts.geometry.drift_cell import DriftCell
from math import atan2, degrees, sqrt


class DTPatch:
    """
    A class to visualize DT Station data.

    Attributes:
    -----------
    bounds_collections : PatchCollection
        A collection of patches representing the bounds of the station and its superlayers.

    cells_collection : PatchCollection
        A collection of patches representing each DT cell, with optional colormap based on time information.
    """

    def __init__(
        self,
        station: Station,
        axes,
        local=True,
        faceview="phi",
        bounds_kwargs=None,
        cells_kwargs=None,
    ):
        """
        Initialize a DTPatch instance.

        :param station: The Station object containing the geometry information.
        :type station: Station
        :param axes: The matplotlib axes to draw the patches on.
        :type axes: matplotlib.axes.Axes
        :param local: Boolean indicating whether to use local or global coordinates.
        :type local: bool, optional
        :param faceview: The view type, either "phi" or "eta".
        :type faceview: str, optional
        :param bounds_kwargs: Additional keyword arguments for the bounds PatchCollection.
        :type bounds_kwargs: dict, optional
        :param cells_kwargs: Additional keyword arguments for the cells PatchCollection.
        :type cells_kwargs: dict, optional
        :return: None. Adds two collections, one for the bounds and another for each DT cell, to the provided matplotlib axes.
        """
        self.current_DT = station
        self.axes = axes
        self.view = faceview
        self.bounds_collections = PatchCollection(
            [], **(bounds_kwargs or {"facecolor": "none", "edgecolor": "k"})
        )
        self.bounds_collections.set_picker(True)
        self.bounds_collections.station = station
        self.cells_collection = PatchCollection(
            [], **(cells_kwargs or {"facecolor": "none", "edgecolor": "k"})
        )

        self.local = local

        if not self.local:  # if global, compute the angle to rotate the patches
            nx, ny, _ = station.direction
            self.angle = (
                degrees(atan2(ny, nx)) + 90
            )  # ang_incline = ang_normal_refx + 90

        # draw Sl bounds
        self._draw_bounds()
        # draw cells
        self._draw_cells()

        # add collections to axes
        axes.add_collection(self.bounds_collections)
        axes.add_collection(self.cells_collection)

    def _draw_bounds(self):
        """
        Draw the bounds of the station and its superlayers.
        """
        frames = []
        # first draw the DT frame
        frames.append(self._create_frame(self.current_DT, type="station"))

        # then draw the superlayer frames
        for super_layer in self.current_DT.super_layers:
            frames.append(self._create_frame(super_layer, type="super_layer"))

        self.bounds_collections.set_paths(frames)

    def _draw_cells(self):
        """
        Draw the cells within the superlayers.
        """
        cells = []
        times = []
        for super_layer in self.current_DT.super_layers:
            if self.view == "phi" and super_layer.number == 2:
                continue  # skip superlayer 2
            elif self.view == "eta" and super_layer.number != 2:
                continue  # skip superlayer 1 and 3
            for layer in super_layer.layers:
                for cell in layer.cells:
                    rotation_point = layer.global_center if not self.local else None
                    cell_patch = self._create_frame(cell, rotation_point, type="cell")
                    time = cell.driftTime

                    cells.append(cell_patch)
                    times.append(time)

        self.cells_collection.set_paths(cells)
        self.cells_collection.set_array(times)

    def _create_frame(self, obj, rotation_point=None, type=None):
        """
        Create a rectangular frame for a given object based on the view type.

        :param obj: The object to create the frame (from mpldts.geometry).
        :type obj: Station, SuperLayer, Layer, or Cell
        :param rotation_point: The point to rotate the frame around (used for global coordinates in phi view).
        :type rotation_point: tuple, optional
        :param type: The type of the object (station, superlayer, or cell).
        :type type: str, optional
        :return: A Rectangle patch representing the frame.
        """
        if self.view == "phi":
            return self._create_frame_phi(obj, rotation_point, type)
        elif self.view == "eta":
            return self._create_frame_eta(obj, type)
        else:
            raise ValueError(f"Unknown view type: {self.view}")

    def _create_frame_phi(self, obj, rotation_point=None, type=None):
        """
        Create a rectangular frame for a given object in the phi view.

        :param obj: The object to create the frame (from mpldts.geometry).
        :type obj: Station, SuperLayer, Layer, or Cell
        :param rotation_point: The point to rotate the frame around (used for global coordinates in phi view).
        :type rotation_point: tuple, optional
        :param type: The type of the object (station, superlayer, or cell).
        :type type: str, optional
        :return: A Rectangle patch representing the frame.
        """
        width, height, length = obj.bounds
        if self.local:
            x_min, y_min, z_min = obj.local_position_at_min
        else:
            x_min, y_min, z_min = obj.global_position_at_min
            x, y, z = obj.global_center

        if type == "super_layer" and obj.number == 2:
            width = length
            x_min = z_min if self.local else x - (length / 2)

        frame = Rectangle((x_min, y_min), width, height)

        if not self.local:
            frame.rotation_point = (
                (rotation_point[0], rotation_point[1]) if rotation_point else (x, y)
            )
            frame.set_angle(self.angle)

        return frame

    def _create_frame_eta(self, obj, type=None):
        """
        Create a rectangular frame for a given object in the eta view.

        :param obj: The object to create the frame (from mpldts.geometry).
        :type obj: Station, SuperLayer, Layer, or Cell
        :param type: The type of the object (station, superlayer, or cell).
        :type type: str, optional
        :return: A Rectangle patch representing the frame.
        """
        width, height, length = obj.bounds
        if self.local:
            x_min, y_min, z_min = obj.local_position_at_min
        else:
            x_min, y_min, z_min = obj.global_position_at_min
            x_min = z_min
            # y_min = sqrt(y_min ** 2 + x_min ** 2)
        if type != "cell" and obj.number != 2:
            width = length
            x_min = z_min
        frame = Rectangle((x_min, y_min), width, height)
        return frame
