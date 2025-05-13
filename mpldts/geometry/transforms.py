import numpy as np
import pytransform3d.transformations as pt
import pytransform3d.rotations as pr

class TransformManager:
    """
    Class to manage the transformation from one reference frame to another.
    """

    def __init__(self, initial_frame="A"):
        self.transform_chain = {
            (initial_frame, initial_frame): np.eye(4),
        }

        self.available_frames = {initial_frame}

    def __str__(self):
        return f"TransformManager ({self.get_available_frames()})"

    def get_available_frames(self):
        return sorted(list(self.available_frames))

    def add(self, from_frame, to_frame, transformation_matrix=None, rotation_matrix=None, translation_vector=None):
        """
        Add a transformation from one frame to another.

        :param from_frame: The reference frame to move the point from.
        :type from_frame: str
        :param to_frame: The reference frame to move the point to.
        :type to_frame: str
        :param transformation_matrix: The transformation matrix for the transformation.
        :type transformation_matrix: ndarray
        :param rotation_matrix: The rotation matrix for the transformation.
        :type rotation_matrix: ndarray
        :param translation_vector: The translation vector for the transformation.
        :type translation_vector: ndarray
        """
        if transformation_matrix is None and (rotation_matrix is None and translation_vector is None):
            raise ValueError("Either a transformation_matrix must be provided, or both rotation_matrix and translation_vector must be provided.")

        if not (isinstance(from_frame, str) and isinstance(to_frame, str)):
            raise TypeError("from_frame and to_frame must be strings.")

        if from_frame == to_frame:
            raise ValueError("Cannot modify the identity transformation.")

        if (from_frame, to_frame) == (from_frame, from_frame):
            raise ValueError("Cannot modify the identity transformation.")

        if transformation_matrix is not None:
            self.transform_chain[(from_frame, to_frame)] = transformation_matrix
        else:
            if rotation_matrix is not None:
                if pr.matrix_requires_renormalization(rotation_matrix):
                    rotation = pr.norm_matrix(rotation_matrix)
                else:
                    rotation = rotation_matrix
            else:
                rotation = np.eye(3) 
            if translation_vector is not None:
                translation = translation_vector
            else:
                translation = np.zeros(3)

            self.transform_chain[(from_frame, to_frame)] = pt.transform_from(rotation, translation)

        self.available_frames.add(from_frame)
        self.available_frames.add(to_frame)

    def remove(self, from_frame, to_frame):
        """
        Remove a defined transformation.
        """
        key = (from_frame, to_frame)
        if key == (from_frame, from_frame):
            raise ValueError("Cannot remove the identity transformation.")
        if key in self.transform_chain:
            del self.transform_chain[key]

    def get_transformation(self, from_frame, to_frame):
        """
        Get the composed transformation matrix from the from_frame to the to_frame.

        :param from_frame: The starting reference frame (str).
        :param to_frame: The ending reference frame (str).
        :return: The 4x4 homogeneous transformation matrix or None if no path found.
        :rtype: ndarray or None
        """
        # Initialize a set to keep track of visited frames
        visited = set()
        # Initialize a stack with the starting frame and an identity transformation matrix
        stack = [(from_frame, np.eye(4))]  # current frame and accumulated transformation

        # Perform a depth-first search to find a path from from_frame to to_frame
        while stack:
            # Pop the current frame and its accumulated transformation from the stack
            current_frame, current_transform = stack.pop()
            # If the current frame is the target frame, return the accumulated transformation
            if current_frame == to_frame:
                return current_transform
            # Mark the current frame as visited
            visited.add(current_frame)
            
            # Iterate through all transformations in the transform chain
            for (src, dst), transform in self.transform_chain.items():
                # If the current frame is the source and the destination is not visited
                if src == current_frame and dst not in visited:
                    # Concatenate the current transformation with the new transformation
                    new_transform = pt.concat(current_transform, transform)
                    # Add the destination frame and the new transformation to the stack
                    stack.append((dst, new_transform))
                # If the current frame is the destination and the source is not visited
                elif dst == current_frame and src not in visited:
                    # Concatenate the current transformation with the inverse of the new transformation
                    new_transform = pt.concat(current_transform, pt.invert_transform(transform))
                    # Add the source frame and the new transformation to the stack
                    stack.append((src, new_transform))

        # If no path is found, return None
        return None

    def transform(self, P, from_frame, to_frame):
        """
        Transform a point from the from_frame to the to_frame.

        :param P: The point(s) to transform (array-like, shape (3,) or (n_points, 3)).
        :param from_frame: The starting reference frame (str).
        :param to_frame: The ending reference frame (str).
        :return: The transformed point(s) (ndarray, shape (3,) or (n_points, 3)).
        """
        if from_frame not in self.available_frames or to_frame not in self.available_frames:
            raise ValueError(f"One or both of the frames '{from_frame}' or '{to_frame}' are not defined.")

        matrix = self.get_transformation(from_frame, to_frame)
        if matrix is None:
            raise ValueError(f"No transformation path found from {from_frame} to {to_frame}.")

        if not isinstance(P, (list, tuple, np.ndarray)):
            raise TypeError("P must be a list, tuple, or ndarray.")

        if len(np.shape(P)) > 1:
            points = pt.vectors_to_points(P)
        else:
            points = pt.vector_to_point(P)

        return pt.transform(matrix, points)[..., :3]


def compute_theta(x, y, z):
    """
    Compute the angle theta from the x, y, z coordinates.

    :param x: The x coordinate.
    :type x: float
    :param y: The y coordinate.
    :type y: float
    :param z: The z coordinate.
    :type z: float
    :return: The angle theta in radians.
    :rtype: float
    """
    if z == 0 and (x == 0 and y == 0):
        raise ValueError("origin point (0, 0, 0) has not a defined theta")

    if x == 0 and y == 0:
        if z > 0:
            return 0.0
        else:
            return np.pi

    r = np.sqrt(x**2 + y**2)

    return np.arctan2(r, z)

def compute_eta(x, y, z):
    """
    Compute the pseudorapidity from the x, y, z coordinates.

    :param x: The x coordinate.
    :type x: float
    :param y: The y coordinate.
    :type y: float
    :param z: The z coordinate.
    :type z: float
    :return: The angle eta in radians.
    :rtype: float
    """
    theta = compute_theta(x, y, z)

    if theta == 0 or theta == np.pi:
        return float('inf')

    eta = -1 * np.log(np.tan(theta / 2))

    return eta

def change_frame(point, from_frame, to_frame):
    """
    Util function to move a point from a DT reference frame to another."

    :param point: The point to move.
    :type point: tuple
    :param from_frame: The reference frame to move the point from. It could be {'SL2', 'Station', 'CMS', 'CMS2'}.
    :type from_frame: str
    :param to_frame: The reference frame to move the point to. It could be {'SL2', 'Station', 'CMS', 'CMS2'}.
    :type to_frame: str
    :return: The point in the new reference frame.

    .. note::
        At the moment only the transformation between SL2 and Station and vice versa are implemented.
    """
    M1 = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])  # SL2 to Station: Rz(pi/2)
    # M2 = array([ # Station to CMS: Rx(-pi/2)
    #     [1, 0, 0],
    #     [0, 0, 1],
    #     [0, -1, 0]
    # ])
    # M3 = array([ # SL2 to CMS:
    #     [0, 0, -1],
    #     [-1, 0, 0],
    #     [0, -1, 0]
    # ])

    matrices = {
        ("SL2", "Station"): M1,
        ("Station", "SL2"): M1.T,
        # ("Station", "CMS"): M2,
        # ("SL2", "CMS"): M3,
        # ("CMS", "Station"): M2.T,
        # ("CMS", "SL2"): M3.T,
    }

    if from_frame == to_frame:
        return point

    if (from_frame, to_frame) not in matrices:
        raise ValueError(f"Transformation from {from_frame} to {to_frame} is not implemented yet.")

    if not isinstance(point, np.ndarray):
        point = np.array(point)

    return tuple(float(cord) for cord in matrices[(from_frame, to_frame)] @ point)
