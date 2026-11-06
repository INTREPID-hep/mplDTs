from mpldts.geometry.segments import Segment, Segments
from mpldts.geometry.station import Station
import numpy as np
from pandas import DataFrame


class AMDTSegment(Segment):
    """
    Represents a DT AM (Analytical Method) trigger primitive segment.

    Each DT AM segment is defined by its geometric center and direction. Two segment types are considered:

    - **Phi segments**: ...
    - **Theta segments**: ...

    """

    def __init__(
        self,
        number,
        parent=None,
        sl=None,
        position=None,
        angle=None,
        reference_frame=None,
        **kwargs,
    ):
        super().__init__()
        self.number = number
        self.sl = sl
        self.reference_frame = reference_frame

        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        if parent is not None:
            if not isinstance(parent, Station):
                raise TypeError("Parent must be an instance of Station.")
            self.parent = parent
        else:
            raise ValueError("Parent station must be provided for the segment.")

        self.wh = getattr(self.parent, "wheel", None)
        self.sc = getattr(self.parent, "sector", None)
        self.st = getattr(self.parent, "number", None)

        self._compute_segment_properties(position, angle)

    def _compute_segment_properties(self, position, angle):
        _dx = -1 * np.sin(np.radians(angle))  # Calculate the x component of the direction vector
        _dz = np.cos(np.radians(angle))  # Calculate the z component of the direction vector

        is_sl2 = self.sl == 2
        _center = [0, -position, 0] if is_sl2 else [position, 0, 0]
        _direction = (
            np.array([0, -_dx, _dz]) if is_sl2 else np.array([_dx, 0, _dz])
        )  # direction vector in local cords

        # check if user specified a reference frame
        # if no reference frame is specified, we assume the provided position and angle are already in the station frame
        rframe = getattr(self, "reference_frame", None) or "Station"
        if rframe not in self.parent.transformer.available_frames:
            raise ValueError(
                f"The specified reference frame '{rframe}' is not available in the parent transformer."
            )

        if rframe != "Station":
            # If the user specified a reference frame, transform the center and direction to the station frame
            _local_center = self.parent.transformer.transform(
                _center, from_frame=rframe, to_frame="Station"
            )
            _local_direction = self.parent.transformer.transform(
                _direction, from_frame=rframe, to_frame="Station", type="vector"
            )
        else:
            _local_center = _center
            _local_direction = _direction

        if (
            self.sl != 0
        ):  # If the segment belongs to SL1, SL2 or SL3, we transform from  vertical cord to SuperLayer frame to center it in SL
            try:
                _local_center[2] = self.parent.super_layer(self.sl).transformer.transform(
                    (0, 0, 0), from_frame=f"SL{self.sl}", to_frame="Station"
                )[2]
            except AttributeError:
                raise ValueError(
                    f"Invalid SuperLayer number '{self.sl}' for the parent station{self.parent.name}. "
                    f"It should be {[sl.number for sl in self.parent.super_layers]}."
                )

        _global_center = self.parent.transformer.transform(
            _local_center, from_frame="Station", to_frame="CMS"
        )  # global center in CMS coordinates
        _global_direction = self.parent.transformer.transform(
            _local_direction, from_frame="Station", to_frame="CMS", type="vector"
        )  # direction in CMS coordinates

        # normalize the direction vectors
        _local_direction = _local_direction / np.sqrt(np.sum(_local_direction**2))
        _global_direction = _global_direction / np.sqrt(np.sum(_global_direction**2))

        # In this way to ensure that they are tuples of floats and not numpy types... (not very important XD)
        self.local_center = tuple(float(i) for i in _local_center)
        self.global_center = tuple(float(i) for i in _global_center)
        self.local_direction = tuple(float(i) for i in _local_direction)
        self.global_direction = tuple(float(i) for i in _global_direction)


class AMDTSegments(Segments):
    """
    Represents a collection of DT AM (Analytical Method) trigger primitive segments.

    Each DT AM segment is defined by its geometric center and direction. Two segment types are considered:

    - **Phi segments**: ...
    - **Theta segments**: ...

    """

    def __init__(self, segs_info=None, reference_frame="SL13Center"):
        """
        Constructor of the Segments class.

        :param segs_info: Information for the segments. It could be a dictionary, a list of dictionaries,
                or a pandas DataFrame containing the segments attributes, they should be identified by
                e.g. ``[{"sl": 1, "angle": 2, "position": 12.2}, ...]``
        :type segs_info: dict, list of dict, or pandas.DataFrame.
        """
        super().__init__()
        if segs_info is None:
            raise ValueError("The segments information must be provided.")

        self._build_segments(segs_info, reference_frame=reference_frame)

    def _build_segments(self, segements_info=None, reference_frame=None):
        """
        Build up the segments of the station. It creates the segments contained in the station and
        sets the attributes.
        """
        if isinstance(segements_info, dict):
            info = [segements_info]
        elif isinstance(segements_info, DataFrame):
            info = segements_info.to_dict(orient="records")
        elif isinstance(segements_info, list):
            info = segements_info
        else:
            raise TypeError(
                "The segments information must be a dictionary, a list of dictionaries, or a pandas DataFrame."
            )

        for i, seg_info in enumerate(info):
            if any(key not in seg_info for key in ["sl", "angle", "position"]):
                raise ValueError(
                    "Each segment information must contain 'sl', 'angle', and 'position' keys."
                )

            # Extract only the required attributes
            sl = seg_info["sl"]
            angle = seg_info["angle"]
            position = seg_info["position"]
            number = seg_info.get("index", i + 1)
            parent = seg_info.get("parent", None)
            wh = seg_info.get("wh", None)
            sec = seg_info.get("sc", None)
            st = seg_info.get("st", None)

            if parent is None and (wh is None or sec is None or st is None):
                raise ValueError(
                    "Either 'parent' must be provided or 'wh', 'sc', and 'st' must be provided."
                )

            if parent is None:
                parent = Station(wheel=wh, sector=sec, station=st)

            # Create Segment and set additional attributes
            _seg = AMDTSegment(
                number,
                parent,
                sl,
                position,
                angle,
                reference_frame=reference_frame,
                **{
                    k: v
                    for k, v in seg_info.items()
                    if k not in ["sl", "angle", "position", "index", "parent", "wh", "sc", "st"]
                },
            )

            self.add(_seg)


if __name__ == "__main__":
    # Example usage
    parent = Station(wheel=2, sector=1, station=3)
    parent2 = Station(wheel=2, sector=1, station=4)
    segments_info = [
        {"parent": parent, "sl": 1, "angle": -10.2, "position": 0},
        {"parent": parent, "sl": 3, "angle": 20.0, "position": 0},
        {"parent": parent, "sl": 2, "angle": 0.1, "position": 10},
        {"parent": parent2, "sl": 1, "angle": -10.2, "position": 0},
    ]
    segments = AMDTSegments(segments_info)
    for seg in segments:
        print(seg)
    print(segments.groupby(["wh", "sc", "st"]))
