from matplotlib.collections import LineCollection
from mpldts.geometry import AMDTSegments
from mpldts.patches.dt_patch_base import DTRelatedPatch
import warnings

class DTSegmentsPatch(DTRelatedPatch):
    """
    A class to visualize a 2D representation of Segments of a DT chamber in matplotlib context.

    Attributes:
    -----------
        segments_collection : matplotlib.collections.LineCollection
            A collection of line segments representing the segments of the station.
        segments : AMDTSegments
            The segments to be visualized.
        axes : matplotlib.axes.Axes
            The matplotlib axes to draw the patches on.
        view : str
            The view type, either "phi" or "eta".
        local : bool
            Boolean indicating whether to use local or global coordinates.
        inverted : bool
            Boolean indicating whether to invert the view. If local is False, this will not have any effect.
        vmap : str
            The variable to map to the colormap.

    .. important::

        Be aware that this is not a child class of ``matplotlib.patches.Patch``. Instead, it creates a
        ``matplotlib.collections.LineCollection`` object to draw the segments as lines.
    """

    def __init__(
        self,
        segments: AMDTSegments,
        axes,
        faceview="phi",
        local=True,
        inverted=False,
        vmap="quality",
        segs_kwargs=None,
        **kwargs,
    ):
        """
        Initialize a SegmentsPatch instance.

        :param segments: The segments objects containing the geometry information.
        :type segments: AMDTSegments
        :param axes: The matplotlib axes to draw the patches on.
        :type axes: matplotlib.axes.Axes
        :param faceview: The view type, either "phi" or "eta".
        :type faceview: str, optional
        :param local: Boolean indicating whether to use local or global coordinates.
        :type local: bool, optional
        :param inverted: Boolean indicating whether to invert the view. If local is False, this will not have any effect.
        :type inverted: bool, optional
        :param vmap: The variable to map to the colormap.
        :type vmap: str, optional
        :param segs_kwargs: Additional keyword arguments to apply to the LineCollection.
        :type segs_kwargs: dict, optional
        :return: None. Adds a collection with the line segments of a chamber to the provided matplotlib axes.
        """
        if faceview == "eta":
            warnings.warn("The 'eta' view is on development and may not work as expected.")
        self.vmap = vmap
        self.segments = segments

        self.segments_collection = LineCollection(
            [], **(segs_kwargs or {"linewidth": 0.8, "color": "k"}), **kwargs
        )

        self.parent = segments[0].parent # All segments should have the same parent

        super().__init__(
            station=self.parent,
            axes=axes,
            faceview=faceview,
            local=local,
            inverted=inverted,
            collections=[self.segments_collection],
        )

    def _draw_collections(self):
        self._draw_segments()

    def _draw_segments(self):
        """
        Draw the segments within the Station.
        """
        paths = []
        vars = []
        for seg in self.segments:
            if self.view == "eta" and seg.sl != 2:
                continue
            if self.view == "phi" and seg.sl == 2:
                continue
            path = self._create_segment(seg)
            var = getattr(seg, self.vmap, 0)

            paths.append(path)
            vars.append(var)

        self.segments_collection.set_paths(paths)
        self.segments_collection.set_array(vars)

    def _create_segment(self, seg):
        """
        Create a segment (line) for the given object.
        """
        x, y, z = seg.local_center
        dx, dy, dz = seg.local_direction
        if seg.sl == 2:
            _, _, length = self.parent.bounds
            x, y = -y, x  # Invert x and y for eta view
            dx, dy = -dy, dx  # Invert direction for eta view

        size = 40

        x_start = x - dx * size * 0.5
        z_start = z - dz * size * 0.5
        x_end = x + dx * size * 0.5
        z_end = z + dz * size * 0.5

        return [[x_start, z_start], [x_end, z_end]]

    def change_vmap(self, vmap):
        """
        Change the variable to map to the colormap.

        :param vmap: The variable to map to the colormap.
        :type vmap: str
        """
        self.vmap = vmap
        vars = [getattr(seg, self.vmap, 0) for seg in self.segments]
        self.segments_collection.set_array(vars)

class MultiDTSegmentsPatch:
    """
    A class to visualize a 2D representation of Segments with multiple parent DT stations in matplotlib context.

    Attributes:
    -----------
        patches : list
            A list of SegmentsPatch instances, one for each parent station.
        axes : matplotlib.axes.Axes
            The matplotlib axes to draw the patches on.
    """

    def __init__(
        self,
        segments: AMDTSegments,
        axes,
        **kwargs,
    ):
        """
        Initialize a MultiSegmentsPatch instance.

        :param segments: The segments objects containing the geometry information.
        :type segments: AMDTSegments
        :param axes: The matplotlib axes to draw the patches on.
        :type axes: matplotlib.axes.Axes
        """
        self.patches = {}

        # Group segments by parent station
        grouped_segments = segments.groupby(["wh", "sc", "st"])

        for key, segs in grouped_segments.items():
            if len(segs) == 0:
                continue
            patch = DTSegmentsPatch(
                segments=segs,
                axes=axes,
                **kwargs,
            )
            self.patches[key] = patch
