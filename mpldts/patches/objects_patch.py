"""Arbitrary objects of a chamber: points and polylines.

A chamber is drawn by :class:~`mpldts.patches.dt_station_patch.DTStationPatch`;
everything that happens inside it (hits, tracks, showers, trigger primitives)
is some set of points or lines. This patch takes them in any frame the station
graph knows and projects them exactly like the cells, so the local/global and
inverted views come from the same place.
"""

import numpy as np
from matplotlib.lines import Line2D

from mpldts.patches.dt_patch_base import DTRelatedPatch

__all__ = ["DTObjectsPatch"]


class DTObjectsPatch(DTRelatedPatch):
    """
    A collection of points or polylines drawn in the view of a DT chamber.

    Attributes:
    -----------
        objects : list
            The `(points, style)` pairs given by the caller.
        frame : str
            The frame the coordinates are expressed in ("Station" by
            default; any name the station graph resolves, "CMS" included).
        axes : matplotlib.axes.Axes
            The matplotlib axes to draw the objects on.
        view : str
            The view type, either "phi" or "eta".
        local : bool
            Boolean indicating whether to use local or global coordinates.
        inverted : bool
            Boolean indicating whether to invert the view. If local is False,
            this will not have any effect.

    The `style` of each object is the keyword arguments of one
    `matplotlib.lines.Line2D`: a single point is a marker
    (`linestyle="None", marker="*"`), two or more are a polyline.

    .. important::

        The coordinates are the ones the cells use: horizontal station x,
        vertical station z, in both views. A line given in `CMS` and the same
        line given in `Station` land on the same pixels; `local=False` and
        `inverted=True` then move the objects exactly like the cells.
    """

    def __init__(
        self,
        station,
        axes,
        objects,
        faceview="phi",
        local=True,
        inverted=False,
        frame="Station",
        **style,
    ):
        """
        Initialize a DTObjectsPatch instance.

        :param station: The Station object containing the geometry information.
        :type station: mpldts.geometry.Station
        :param axes: The matplotlib axes to draw the objects on.
        :type axes: matplotlib.axes.Axes
        :param objects: `(points, style)` pairs; `points` is an (N, 3)
            array in `frame` and `style` a dict of Line2D keyword
            arguments.
        :type objects: iterable of (array-like, dict)
        :param faceview: The view type, either "phi" or "eta".
        :type faceview: str, optional
        :param local: Boolean indicating whether to use local or global coordinates.
        :type local: bool, optional
        :param inverted: Boolean indicating whether to invert the view.
        :type inverted: bool, optional
        :param frame: The frame the points are expressed in.
        :type frame: str, optional
        :param style: Keyword arguments applied to every object (each object's
            own style wins).
        :return: None. Adds one line artist per object to the axes.
        """
        self.frame = frame
        self.objects = [
            (np.asarray(points, dtype=float).reshape(-1, 3), dict(object_style))
            for points, object_style in objects
        ]
        self.lines = [
            Line2D([], [], **{**style, **object_style})
            for _, object_style in self.objects
        ]

        super().__init__(
            station=station,
            axes=axes,
            collections=self.lines,
            faceview=faceview,
            local=local,
            inverted=inverted,
        )

    def _draw_collections(self):
        self._draw_objects()

    def _draw_objects(self):
        for line, (points, _style) in zip(self.lines, self.objects):
            face = self._to_face(points)
            line.set_data(face[:, 0], face[:, 1])

    def _to_face(self, points):
        """The coordinates the cells are drawn at: (station x, station z).

        The two views differ in *which* super layers they show, not in the pair
        of axes: #BT#DTStationPatch#BT# draws every cell at its station x and z, so an
        object has to land on those numbers or it does not sit on its cell. The
        view still drives the local/global and inverted transforms above.
        """
        local = self.station.transformer.transform(
            points, from_frame=self.frame, to_frame="Station"
        )
        return np.column_stack([local[:, 0], local[:, 2]])
