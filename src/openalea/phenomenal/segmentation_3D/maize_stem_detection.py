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
from __future__ import absolute_import

import networkx
import numpy
import scipy.interpolate
import scipy.spatial
from scipy.signal import savgol_filter

from openalea.phenomenal.segmentation_3D.peak_detection import (
    peak_detection)

from .plane_interception import (
    intercept_points_along_path_with_planes,
    intercept_points_along_polyline_with_ball,
    max_distance_in_points)

# ==============================================================================


def maize_stem_peak_detection(closest_nodes_plane, stop_index):
    nodes_length = map(float, map(len, closest_nodes_plane))

    window_length = max(4, len(nodes_length) / 8)
    window_length = window_length + 1 if window_length % 2 == 0 else window_length

    nodes_length_smooth = savgol_filter(numpy.array(nodes_length),
                                        window_length=window_length,
                                        polyorder=3)

    nodes_length_smooth = list(nodes_length_smooth)

    lookahead = 1
    max_peaks, min_peaks = peak_detection(nodes_length_smooth, lookahead)

    min_peaks = [(i, v) for i, v in min_peaks if i <= stop_index]
    min_peaks = [(0, nodes_length_smooth[0]),
                 (1, nodes_length_smooth[1])] + min_peaks
    min_peaks = list(set(min_peaks))

    return min_peaks


def get_nodes_radius(center, points, radius):
    x, y, z = center

    result = numpy.sqrt((points[:, 0] - x) ** 2 +
                        (points[:, 1] - y) ** 2 +
                        (points[:, 2] - z) ** 2)

    index = numpy.where(result <= numpy.array(radius))
    result = set(map(tuple, list(points[index])))

    return result


def stem_detection(stem_segment_voxel, stem_segment_path, voxels_size,
                   graph=None,
                   distance_plane=1.00):

    # ==========================================================================

    arr_stem_segment_voxel = numpy.array(list(stem_segment_voxel))
    arr_stem_segment_path = numpy.array(stem_segment_path)

    closest_nodes_planes, _ = intercept_points_along_path_with_planes(
        arr_stem_segment_voxel,
        arr_stem_segment_path,
        distance_from_plane=distance_plane * voxels_size,
        voxels_size=voxels_size,
        points_graph=graph)

    arr_closest_nodes_planes = [numpy.array(list(nodes)) for nodes in
                                closest_nodes_planes]

    distances = list()
    for i in range(len(arr_closest_nodes_planes)):
        distance = max_distance_in_points(arr_closest_nodes_planes[i])
        distances.append(float(distance))
    ball_radius = max(distances) / 2.0

    closest_nodes_ball = intercept_points_along_polyline_with_ball(
        arr_stem_segment_voxel,
        graph,
        arr_stem_segment_path,
        ball_radius=ball_radius)

    nodes_length = map(float, map(len, closest_nodes_ball))
    index_20_percent = int(float(len(nodes_length)) * 0.20)
    nodes_length[:index_20_percent] = [0] * index_20_percent
    stop_index = nodes_length.index((max(nodes_length)))
    min_peaks_stem = maize_stem_peak_detection(arr_closest_nodes_planes,
                                               stop_index)

    window_length = max(4, len(nodes_length) / 8)
    window_length = window_length + 1 if window_length % 2 == 0 else window_length
    distances = savgol_filter(numpy.array(distances),
                              window_length=window_length,
                              polyorder=2)
    # ==========================================================================

    stem_segment_centred_path = [
        nodes.mean(axis=0) for nodes in arr_closest_nodes_planes]

    stem_voxel = set()
    radius = dict()
    stem_centred_path_min_peak = list()
    max_index_min_peak = 0

    for index, _ in min_peaks_stem:
        max_index_min_peak = max(max_index_min_peak, index)
        radius[index] = distances[index] / 2.0
        stem_centred_path_min_peak.append(stem_segment_centred_path[index])
        stem_voxel = stem_voxel.union(closest_nodes_planes[index])

    # ==========================================================================
    # Interpolate

    arr_stem_centred_path_min_peak = numpy.array(
        stem_centred_path_min_peak).transpose()

    k = 2
    if len(stem_centred_path_min_peak) <= k:
        k = 1

    tck, u = scipy.interpolate.splprep(arr_stem_centred_path_min_peak, k=k)
    xxx, yyy, zzz = scipy.interpolate.splev(numpy.linspace(0, 1, 500), tck)

    # ==========================================================================

    arr_stem_voxels = set()
    for nodes in closest_nodes_planes[:max_index_min_peak + 1]:
        arr_stem_voxels = arr_stem_voxels.union(set(nodes))
    arr_stem_voxels = numpy.array(list(arr_stem_voxels))

    # ==========================================================================

    real_path = list()
    for i in range(len(xxx)):

        index = int(i * max_index_min_peak / 500.0)
        ii = min([ind for ind in radius.keys() if index < ind])
        r = radius[ii]

        x, y, z = xxx[i], yyy[i], zzz[i]
        real_path.append((x, y, z))
        result = get_nodes_radius((x, y, z), arr_stem_voxels, r)
        stem_voxel = stem_voxel.union(result)

    not_stem_voxel = stem_segment_voxel - stem_voxel
    stem_path = arr_stem_segment_path[:max_index_min_peak + 1]
    stem_top = set(closest_nodes_planes[max_index_min_peak])

    return stem_voxel, not_stem_voxel, stem_path, stem_top

