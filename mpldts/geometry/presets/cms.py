"""CMS preset: the frames that only a CMS chamber has (T-031).

SectorRef and SL13Center encode facts of the CMS chambers, not of a generic
station: the sector phi line used by the AM trigger primitives (MB4 sectors 4
and 10 are divided into 13 and 14) and the geometrical centre of the super
layers 1 and 3. The CMS path applies them; a station built from a spec gets the
natural views from its own pose and nothing else.

No XML, no plotting import: the preset reads the record and the node poses.
"""

from dataclasses import replace

import numpy as np

from mpldts.geometry.sources.cms_xml import NEGATIVE_FACE_SECTORS
from mpldts.geometry.specs import AttachmentSpec, Box, Pose

__all__ = ["NEGATIVE_FACE_SECTORS", "face_factor", "add_frames", "with_attachments"]


def face_factor(wheel, sector):
    """-1 for negative wheels, 1 for positive; wheel 0 depends on the sector.

    Details in https://dt-sx5.web.cern.ch/dt-sx5/run/docs/050912DT_type_naming.pdf
    """
    if wheel < 0:
        return -1
    if wheel > 0:
        return 1
    return -1 if sector in NEGATIVE_FACE_SECTORS else 1


def add_frames(graph, node, record, wheel, sector):
    """Register SectorRef and SL13Center on a CMS chamber (T-031)."""
    station_frame = node.frame_id

    def add(name, pose):
        graph.add_virtual(station_frame + "/" + name, station_frame, pose)

    face = face_factor(wheel, sector)

    # Sector phi line (AM trigger primitives). MB4 sectors 4 and 10 are
    # divided into 13 and 14, hence the sign correction.
    x, y, _ = record["global"]
    correction = 1
    if sector in (13, 14):
        correction = -1
        sector = 4 if sector == 13 else 10
    dphi = np.arctan2(y, x) - (sector - 1) * np.pi / 6 * correction
    dx = -np.sin(dphi) * np.hypot(x, y) * face * correction
    add("SectorRef", Pose.translated(-dx, 0.0, 0.0))

    # Geometrical center of the super layers 1 and 3
    sl1 = next((sl for sl in record["super_layers"] if sl["number"] == 1), None)
    sl3 = next((sl for sl in record["super_layers"] if sl["number"] == 3), None)
    if sl1 is not None and sl3 is not None:
        centre = (np.asarray(sl1["local"]) + np.asarray(sl3["local"])) / 2.0
        add("SL13Center", Pose.translated(*centre))


def with_attachments(spec, record):
    """The aluminium honeycomb panel of a CMS chamber (T-032).

    The panel is the box that fills the gap between the super layer 1 and the
    super layer 2 (3 for an MB4 chamber), 1 cm clear of the chamber bounds, as
    the simulator builds it. The XML carries no honeycomb, so it is derived from
    the super layer records here.
    """
    members = {super_layer["number"]: super_layer for super_layer in record["super_layers"]}
    upper = members.get(1)
    lower = members.get(2) or members.get(3)
    if upper is None or lower is None:
        return spec

    upper_bottom = upper["local"][2] - upper["bounds"][1] / 2.0
    lower_top = lower["local"][2] + lower["bounds"][1] / 2.0
    gap = upper_bottom - lower_top
    if gap <= 1.0:
        return spec

    width, _, length = record["bounds"]
    panel = AttachmentSpec(
        name="Honeycomb",
        pose=Pose.translated(0.0, 0.0, (lower_top + upper_bottom) / 2.0),
        shape=Box(width - 1.0, length - 1.0, gap - 1.0),
    )
    return replace(spec, attachments=[panel])
