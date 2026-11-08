"""Detector-family presets: the conventions of one geometry (T-031).

A preset adds the frames and the facts that belong to one detector family and
not to the generic model. The CMS preset is the only one today.
"""

from mpldts.geometry.presets import cms

__all__ = ["cms"]
