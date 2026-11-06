import os
import re
import xml.etree.ElementTree as ET
from functools import lru_cache



class DTGeometry:
    """
    A class to easy access to the CMS DT Geometry from the XML file.

    Attributes
    ----------
    root : xml.etree.ElementTree.Element
        The root element of the parsed XML tree.
    """

    def __init__(self, xml_file):
        """
        Initialize the DTGeometry object by parsing the XML file.

        :param xml_file: Path to the XML file containing the DT Geometry.
        :type xml_file: str
        """
        tree = ET.parse(xml_file)
        self.root = tree.getroot()
        self._rawid_index = {}
        self._chamber_key_index = {}
        self._build_indexes()

    def _build_indexes(self):
        """Build fast lookup indexes from the geometry XML tree."""
        chamber_pattern = re.compile(r"Wh:(-?\d+)\s+St:(\d+)\s+Se:(\d+)")

        for element in self.root.iter():
            raw_id = element.get("rawId")
            if raw_id is not None:
                self._rawid_index[str(raw_id)] = element

            if element.tag == "Chamber":
                chamber_id = element.get("Id", "")
                match = chamber_pattern.search(chamber_id)
                if match:
                    wh, st, sec = (int(v) for v in match.groups())
                    self._chamber_key_index[(wh, sec, st)] = element

    @staticmethod
    def _find_descendant_by_attr(parent, tag, attr_name, attr_value):
        """Find first descendant by tag and attribute value."""
        target = str(attr_value)
        for element in parent.iter(tag):
            if element.get(attr_name) == target:
                return element
        return None

    def _resolve_element(self, raw_id=None, wh=None, sec=None, st=None, sl=None, l=None, w=None):
        """Resolve an XML element from query parts without costly XPath scans."""
        element = self.root

        if raw_id is not None:
            element = self._rawid_index.get(str(raw_id))
        elif wh is not None and sec is not None and st is not None:
            element = self._chamber_key_index.get((int(wh), int(sec), int(st)))

        if element is None:
            return None

        if sl is not None:
            element = self._find_descendant_by_attr(element, "SuperLayer", "superLayerNumber", sl)
            if element is None:
                return None

        if l is not None:
            element = self._find_descendant_by_attr(element, "Layer", "layerNumber", l)
            if element is None:
                return None

        if w is not None:
            element = self._find_descendant_by_attr(element, "Wire", "wireNumber", w)

        return element

    @staticmethod
    def _build_query_str(raw_id=None, wh=None, sec=None, st=None, sl=None, l=None, w=None):
        """Build query-like string for user-facing errors."""
        query = "."
        if raw_id is not None:
            query += f"//*[@rawId='{raw_id}']"
        if wh is not None and sec is not None and st is not None:
            query += "//Chamber"
            query += f"[@Id=' Wh:{wh} St:{st} Se:{sec} ']"
        if sl is not None:
            query += "//SuperLayer"
            query += f"[@superLayerNumber='{sl}']"
        if l is not None:
            query += "//Layer"
            query += f"[@layerNumber='{l}']"
        if w is not None:
            query += "//Wire"
            query += f"[@wireNumber='{w}']"
        return query

    @lru_cache(maxsize=50000)
    def _get_cached(self, attribute=None, raw_id=None, wh=None, sec=None, st=None, sl=None, l=None, w=None):
        """Cached internal resolver with normalized query keys."""
        element = self._resolve_element(raw_id=raw_id, wh=wh, sec=sec, st=st, sl=sl, l=l, w=w)
        query = self._build_query_str(raw_id=raw_id, wh=wh, sec=sec, st=st, sl=sl, l=l, w=w)

        if attribute is None:
            if element is None:
                raise ValueError(f"Element not found for query: {query}")
            return element

        if element is not None:
            if attribute in ["GlobalPosition", "LocalPosition", "NormalVector"]:
                try:
                    x, y, z = self._transform_to_pos(str_pos_tuple=element.find(attribute).text)
                except AttributeError:
                    x, y, z = self._transform_to_pos(str_pos_tuple=element.get(attribute))
                return x, y, z
            elif attribute == "Bounds":
                width, height, length = element.find(attribute).attrib.values()
                return (float(width), float(height), float(length))
            elif "wire" in attribute.lower():
                element = element.find(".//Wires")
                width, height, length, first, last = element.attrib.values()
                if attribute == "WiresSize":
                    return (float(width), float(height), float(length))
                elif attribute == "WiresRange":
                    return (int(first), int(last))
                else:
                    return element
            else:
                sub_element = element.find(attribute)
                if sub_element is not None:
                    return sub_element
                else:
                    try:
                        return element.get(attribute)
                    except AttributeError:
                        raise ValueError(
                            f"Attribute or element '{attribute}' not found for query: {query}"
                        )

        raise ValueError(f"Element not found for query: {query}")

    def get(self, attribute=None, **kwargs):
        """
        Retrieve specific attributes or elements from the XML based on the provided criteria.

        :param attribute: The attribute to retrieve (e.g., 'GlobalPosition', 'LocalPosition', 'Bounds').
        :type attribute: str, optional
        :param kwargs: Additional criteria to filter the elements (e.g., rawId, wh, sec, st, sl, l).
        :type kwargs: dict
        :return: The requested attribute values or element.
        :rtype: tuple, str, or xml.etree.ElementTree.Element
        :raises ValueError: If the element or attribute is not found for the given query.
        """
        raw_id = kwargs.get("rawId")
        wh = kwargs.get("wh")
        sec = kwargs.get("sec")
        st = kwargs.get("st")
        sl = kwargs.get("sl")
        l = kwargs.get("l")
        w = kwargs.get("w")

        return self._get_cached(
            attribute=attribute,
            raw_id=str(raw_id) if raw_id is not None else None,
            wh=int(wh) if wh is not None else None,
            sec=int(sec) if sec is not None else None,
            st=int(st) if st is not None else None,
            sl=int(sl) if sl is not None else None,
            l=int(l) if l is not None else None,
            w=int(w) if w is not None else None,
        )

    @staticmethod
    def _transform_to_pos(str_pos_tuple):
        """
        Transform a string representation of coordinates into a tuple of floats.

        :param str: The string containing the coordinates.
        :type str: str
        :param local: Flag to determine if the coordinates are local or global.
        :type local: bool, optional
        :return: A tuple containing the transformed coordinates.
        :rtype: tuple
        """
        cords = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str_pos_tuple)
        x, y, z = (float(cord) for cord in cords)
        return (x, y, z)


# Initialize the DTGeometry object with the path to the XML file
DTGEOMETRY = DTGeometry(os.path.join(os.path.dirname(__file__), "DTGeometry_v3.xml"))

# Example usage
if __name__ == "__main__":
    dt_geometry = DTGeometry(os.path.abspath("./DTGeometry_v3.xml"))

    # Retrieve and print global and local positions, and bounds for specific chambers
    global_pos_1 = dt_geometry.get("GlobalPosition", wh=-2, sec=1, st=1)
    local_pos_1 = dt_geometry.get("GlobalPosition", wh=-1, sec=1, st=4)
    bounds = dt_geometry.get("Bounds", wh=-1, sec=1, st=4)
    print(f"Bounds for Wh:-1, Sec:1, St:4: {bounds}")

    print(f"Global position for Wh:-2, Sec:1, St:1: {global_pos_1}")
    print(f"Local position for Wh:1, Sec:1, St:4: {local_pos_1}")

    # Iterate through all layers in a specific SuperLayer and print their attributes
    # 1. by using the root element
    for layer in dt_geometry.root.find(".//SuperLayer[@rawId='574922752']").iter("Layer"):
        print("Layer", layer.attrib)
        break
    # 2. by using the get method
    for layer in dt_geometry.get(rawId="574922752").iter("Layer"):
        print("Layer", layer.attrib)
        break
    # Test retrieving attributes of a specific SuperLayer
    print("Super_Layer", dt_geometry.get(rawId=574922752).attrib)
