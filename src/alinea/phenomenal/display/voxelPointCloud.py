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
from alinea.phenomenal.display.voxels import (
    show_voxels,
    screenshot_voxels)
# ==============================================================================


def show_voxel_point_cloud(voxel_point_cloud,
                           color=None,
                           figure_name="",
                           size=(800, 700),
                           with_center_axis=False,
                           azimuth=None,
                           elevation=None,
                           distance=None,
                           focalpoint=None):

    show_voxels(voxel_point_cloud.voxels_position,
                voxel_point_cloud.voxels_size,
                color=color,
                figure_name=figure_name,
                size=size,
                with_center_axis=with_center_axis,
                azimuth=azimuth,
                elevation=elevation,
                distance=distance,
                focalpoint=focalpoint)


def screenshot_voxel_point_cloud(voxel_point_cloud,
                                 color=None,
                                 figure_name="",
                                 size=(800, 700),
                                 with_center_axis=False,
                                 azimuths=None,
                                 elevation=None,
                                 distance=None,
                                 focalpoint=None):

    return screenshot_voxels(voxel_point_cloud.voxels_position,
                             voxel_point_cloud.voxels_size,
                             color=color,
                             figure_name=figure_name,
                             size=size,
                             with_center_axis=with_center_axis,
                             azimuths=azimuths,
                             elevation=elevation,
                             distance=distance,
                             focalpoint=focalpoint)
