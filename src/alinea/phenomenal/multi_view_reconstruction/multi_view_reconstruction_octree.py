# -*- python -*-
#
#       Copyright 2015 INRIA - CIRAD - INRA
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
# ==============================================================================
from __future__ import division, print_function

import collections
import math
import numpy

from alinea.phenomenal.multi_view_reconstruction.multi_view_reconstruction \
    import (get_bounding_box_voxel_projected,
            voxel_is_visible_in_image,)

from alinea.phenomenal.data_structure import Octree


# ==============================================================================


def voxel_is_fully_visible_in_image(voxel_center,
                                    voxel_size,
                                    image,
                                    projection):

    height_image, length_image = image.shape

    # ==========================================================================

    x_min, x_max, y_min, y_max = get_bounding_box_voxel_projected(
        voxel_center, voxel_size, projection)

    x_min = int(min(max(math.floor(x_min), 0), length_image - 1))
    x_max = int(min(max(math.ceil(x_max), 0), length_image - 1))
    y_min = int(min(max(math.floor(y_min), 0), height_image - 1))
    y_max = int(min(max(math.ceil(y_max), 0), height_image - 1))

    # ==========================================================================

    if numpy.all(image[y_min:y_max + 1, x_min:x_max + 1] > 0):
        return True

    return False


def kept_visible(leaf_nodes,
                 images_projections,
                 error_tolerance=0):
    """
    Kept in a new collections.deque the voxel who is visible on each image of
    images_projections according the error_tolerance

    Parameters
    ----------
    voxel_centers : [(x, y, z)]
        cList (collections.deque) of center position of voxel

    voxel_size : float
        Size of side geometry of voxel

    images_projections : [(image, projection), ...]
        List of tuple (image, projection) where image is a binary image
        (numpy.ndarray) and function projection (function (x, y, z) -> (x, y))
        who take (x, y, z) position on return (x, y) position according space
        representation of this image

    error_tolerance : int, optional
        Number of image will be ignored if the projected voxel is not visible.

    Returns
    -------
    out : collections.deque
        List of visible voxel projected on each image according
        the error_tolerance

    """
    kept = collections.deque()
    for leaf in leaf_nodes:

        voxel_center = leaf.position
        voxel_size = leaf.size
        negative_weight = 0

        for image, projection in images_projections:
            if not voxel_is_visible_in_image(
                    voxel_center, voxel_size, image, projection):
                negative_weight += 1
                if negative_weight > error_tolerance:
                    break

        if negative_weight <= error_tolerance:
            kept.append(leaf)

        else:
            leaf.data = False

    return kept


def remove_surrounded(leaf_nodes):
    kept = collections.deque()
    for leaf in leaf_nodes:

        if not leaf.is_surrender():
            kept.append(leaf)

    return kept


def remove_surrounded_fully_visible(leaf_nodes,
                                    images_projections,
                                    error_tolerance=0):
    kept = collections.deque()
    for leaf in leaf_nodes:

        if leaf.is_surrender():

            voxel_center = leaf.position
            voxel_size = leaf.size
            negative_weight = 0

            for image, projection in images_projections:
                if not voxel_is_fully_visible_in_image(
                        voxel_center, voxel_size, image, projection):
                    negative_weight += 1
                    if negative_weight > error_tolerance:
                        break

            if not negative_weight <= error_tolerance:
                kept.append(leaf)

        else:
            kept.append(leaf)

    return kept


# ==============================================================================

def reconstruction_3d(images_projections,
                      voxel_size=4,
                      error_tolerance=0,
                      voxel_center_origin=(0.0, 0.0, 0.0),
                      world_size=4096,
                      verbose=False):
    """
    Construct a list of voxel represented object with positive value on binary
    image in images of images_projections.

    Parameters
    ----------
    images_projections : [(image, projection), ...]
        List of tuple (image, projection) where image is a binary image
        (numpy.ndarray) and function projection (function (x, y, z) -> (x, y))
        who take (x, y, z) position on return (x, y) position according space
        representation of this image

    voxel_size : float, optional
        Size of side geometry of voxel that each voxel will have

    error_tolerance : int, optional


    voxel_center_origin : (x, y, z), optional
        Center position of the first original voxel, who will be split.

    world_size: int, optional
        Minimum size that the origin voxel size must include at beginning

    voxel_centers : collections.deque, optional
        List of first original voxel who will be split. If None, a list is
        create with the voxel_center_origin value.

    verbose : bool, optional
        If True, print for each iteration of split, number of voxel before and
        after projection on images

    Returns
    -------
    out : collections.deque
        List of visible voxel projected on each image according
        the error_tolerance
    """

    if len(images_projections) == 0:
        raise ValueError("images_projection list is empty")

    oc = Octree.from_position(voxel_center_origin, world_size, True)

    leaf_nodes = collections.deque()
    leaf_nodes.append(oc.root)

    nb_iteration = 0
    while voxel_size < world_size:
        voxel_size *= 2.0
        nb_iteration += 1

    for i in range(nb_iteration):

        l = collections.deque()
        for leaf in leaf_nodes:
            l.extend(leaf.creates_sons())

        leaf_nodes = l

        if verbose is True:
            print('Iteration', i + 1, '/', nb_iteration, end="")
            print(' : ', len(leaf_nodes), end="")

        leaf_nodes = kept_visible(leaf_nodes,
                                  images_projections,
                                  error_tolerance)

        # if i + 1 < nb_iteration:
        #     leaf_nodes = remove_surrounded_fully_visible(leaf_nodes,
        #                                                  images_projections,
        #                                                  error_tolerance)

        if verbose is True:
            print(' - ', len(leaf_nodes))

    return oc