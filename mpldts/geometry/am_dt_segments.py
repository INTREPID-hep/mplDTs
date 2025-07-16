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
    def __init__(self, number, parent=None, sl=None, position=None, angle=None):
        super().__init__()
        self.number = number
        self.sl = sl

        if parent is not None:
            if not isinstance(parent, Station):
                raise TypeError("Parent must be an instance of Station.")
            self.parent = parent
            if "TPsFrame" not in parent.transformer.available_frames:
                self._update_transformer()  # Add the AM Tps transformation to the parent transformer

        self.wh = getattr(self.parent, "wheel", None)
        self.sc = getattr(self.parent, "sector", None)
        self.st = getattr(self.parent, "number", None)

        self._compute_segment_properties(position, angle)

    def _update_transformer(self):
        """
        Add to the parent transformer the transformation to move from the AM Trigger primitives frame
        to the Station frame. The TPs frame is defined as the geometrical center of the super layers 1 and 3.
        The transformation is added to the parent station's transformer with the name "TPsFrame".
        """
        sl1_center = np.array(self.parent.super_layer(1).local_center)
        sl3_center = np.array(self.parent.super_layer(3).local_center)
        sls_center = (sl1_center + sl3_center) / 2

        # Translation vector to move the center of TPs frame to the Station Frame
        self.parent.transformer.add("TPsFrame", "Station", translation_vector=sls_center)

    def _compute_segment_properties(self, position, angle):
        _dx = -1* np.sin(np.radians(angle))  # Calculate the x component of the direction vector
        _dz = np.cos(np.radians(angle))  # Calculate the z component of the direction vector

        _center = (position, 0, 0) if self.sl!=2 else (0, -position, 0)
        _local_center = self.parent.transformer.transform(_center, from_frame="TPsFrame", to_frame="Station")# local center in station coordinates
        _global_center = self.parent.transformer.transform(_local_center, from_frame="Station", to_frame="CMS")  # global center in CMS coordinates

        _direction = np.array([_dx, 0, _dz]) if self.sl!=2 else np.array([0, -_dx,_dz]) # direction vector in local cords
        _local_direction = self.parent.transformer.transform(_direction, from_frame="TPsFrame", to_frame="Station", type="vector")  # direction in station coordinates
        _global_direction = self.parent.transformer.transform(_local_direction, from_frame="Station", to_frame="CMS", type="vector")  # direction in CMS coordinates

        # normalize the direction vectors
        _local_direction = _local_direction /np.sqrt(np.sum(_local_direction**2))
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

    def __init__(self, segs_info=None):
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

        self._build_segments(segs_info)

    def _build_segments(self, segements_info=None):
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

            _seg = AMDTSegment(number, parent, sl, position, angle)

            # Set additional attributes
            for key, value in seg_info.items():
                if key not in ["sl", "angle", "position", "index", "parent", "wh", "sc", "st"]:
                    setattr(_seg, key, value)

            self.add(_seg)

if __name__ == "__main__":
    # Example usage
    parent = Station(wheel=2, sector=1, station=3)
    parent2 = Station(wheel=2, sector=1, station=4)
    segments_info = [
        {"parent": parent, "sl":1, "angle": -10.2, "position": 0},
        {"parent": parent, "sl":3, "angle": 20.0, "position": 0},
        {"parent": parent, "sl":2, "angle": 0.1, "position": 10},
        {"parent": parent2, "sl":1, "angle": -10.2, "position": 0},
    ]
    segments = AMDTSegments(segments_info)
    for seg in segments:
        print(seg)
    print(segments.groupby(["wh", "sc", "st"]))

