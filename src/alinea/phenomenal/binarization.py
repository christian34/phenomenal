# -*- python -*-
# -*- coding:utf-8 -*-
#
#       Copyright 2015 INRIA - CIRAD - INRA
#
#       File author(s):
#
#       File contributor(s):
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
# ==============================================================================
""" Binarization routines for PhenoArch/ images """
# ==============================================================================
import numpy
import cv2

import alinea.phenomenal.opencv_wrapping as ocv2
import alinea.phenomenal.binarization_post_processing
import alinea.phenomenal.binarization_algorithm
from alinea.phenomenal.binarization_factor import BinarizationFactor
from alinea.phenomenal.binarization_algorithm import (mean_shift_binarization,
                                                      hsv_binarization)


# ==============================================================================


def side_binarization_routine_mean_shift(image,
                                         mean_image,
                                         threshold=0.3,
                                         dark_background=False,
                                         hsv_min=(30, 11, 0),
                                         hsv_max=(129, 254, 141),
                                         mask_mean_shift=None,
                                         mask_hsv=None,
                                         mask_clean_noise=None):

    binary_hsv_image = hsv_binarization(image, hsv_min, hsv_max, mask_hsv)

    binary_mean_shift_image = mean_shift_binarization(
        image, mean_image, threshold, dark_background, mask_mean_shift)

    result = cv2.add(binary_hsv_image, binary_mean_shift_image * 255)

    result = alinea.phenomenal.binarization_post_processing.clean_noise(
        result, mask_clean_noise)

    return result


def side_binarization_routine_elcom(image,
                                    mean_image,
                                    threshold=0.3,
                                    dark_background=False,
                                    hsv_min=(30, 25, 0),
                                    hsv_max=(150, 254, 165),
                                    mask_mean_shift=None,
                                    mask_hsv=None):

    binary_hsv_image = hsv_binarization(image, hsv_min, hsv_max, mask_hsv)

    binary_mean_shift_image = mean_shift_binarization(
        image, mean_image, threshold, dark_background, mask_mean_shift)

    result = cv2.add(binary_hsv_image, binary_mean_shift_image * 255)

    result = cv2.medianBlur(result, 3)

    return result


def side_binarization_routine_hsv(image,
                                  cubicle_domain,
                                  cubicle_background,
                                  main_hsv_min,
                                  main_hsv_max,
                                  main_mask,
                                  orange_band_mask,
                                  pot_hsv_min,
                                  pot_hsv_max,
                                  pot_mask):
    """
    Binarization of side image for Lemnatech cabin based on hsv segmentation.

    Based on Michael pipeline
    """
    # elementMorph = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    # ==========================================================================
    # Check Parameters
    if not isinstance(image, numpy.ndarray):
        raise TypeError('image should be a numpy.ndarray')

    if image.ndim != 3:
        raise ValueError('image should be 3D array')
    # ==========================================================================

    c = cubicle_domain
    image_cropped = image[c[0]:c[1], c[2]:c[3]]
    hsv_image = cv2.cvtColor(image_cropped, cv2.COLOR_BGR2HSV)

    # ==========================================================================
    # Main area segmentation
    main_area_seg = cv2.medianBlur(hsv_image, ksize=9)
    main_area_seg = cv2.inRange(main_area_seg, main_hsv_min, main_hsv_max)

    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    main_area_seg = cv2.dilate(main_area_seg, element, iterations=2)
    main_area_seg = cv2.erode(main_area_seg, element, iterations=2)

    mask_cropped = main_mask[c[0]:c[1], c[2]:c[3]]
    main_area_seg = cv2.bitwise_and(main_area_seg,
                                    main_area_seg,
                                    mask=mask_cropped)

    # ==========================================================================
    # Band area segmentation
    background_cropped = cubicle_background[c[0]:c[1], c[2]:c[3]]
    hsv_background = cv2.cvtColor(background_cropped, cv2.COLOR_BGR2HSV)
    grayscale_background = hsv_background[:, :, 0]

    grayscale_image = hsv_image[:, :, 0]

    band_area_seg = cv2.subtract(grayscale_image, grayscale_background)
    retval, band_area_seg = cv2.threshold(band_area_seg,
                                          122,
                                          255,
                                          cv2.THRESH_BINARY)

    mask_cropped = orange_band_mask[c[0]:c[1], c[2]:c[3]]
    band_area_seg = cv2.bitwise_and(band_area_seg,
                                    band_area_seg,
                                    mask=mask_cropped)

    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    band_area_seg = cv2.dilate(band_area_seg, element, iterations=5)
    band_area_seg = cv2.erode(band_area_seg, element, iterations=5)

    # ==========================================================================
    # Pot area segmentation
    pot_area_seg = cv2.inRange(hsv_image, pot_hsv_min, pot_hsv_max)

    mask_cropped = pot_mask[c[0]:c[1], c[2]:c[3]]
    pot_area_seg = cv2.bitwise_and(pot_area_seg,
                                   pot_area_seg,
                                   mask=mask_cropped)

    # ==========================================================================
    # Full segmented image
    image_seg = cv2.add(main_area_seg, band_area_seg)
    image_seg = cv2.add(image_seg, pot_area_seg)

    image_out = numpy.zeros([image.shape[0], image.shape[1]], 'uint8')
    image_out[c[0]:c[1], c[2]:c[3]] = image_seg

    return image_out


def side_binarization_routine_adaptive_threshold(image, mask):
    """
    Binarization of side image based on adaptive threshold algorithm of cv2
    """
    # ==========================================================================
    # Check Parameters
    if not isinstance(image, numpy.ndarray):
        raise TypeError('image should be a numpy.ndarray')
    if image.ndim != 3:
        raise ValueError('image should be 3D array')

    if mask is not None:
        if not isinstance(mask, numpy.ndarray):
            raise TypeError('mask should be a numpy.ndarray')
        if mask.ndim != 2:
            raise ValueError('image should be 2D array')

        if image.shape[0:2] != mask.shape:
            raise ValueError('image and mask should have the same shape')
    # ==========================================================================

    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if mask is not None:
        img = cv2.bitwise_and(img, img, mask=mask)

    block_size, c = (41, 20)
    result1 = cv2.adaptiveThreshold(img,
                                    255,
                                    cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY_INV,
                                    block_size,
                                    c)

    block_size, c = (399, 45)
    result2 = cv2.adaptiveThreshold(img,
                                    255,
                                    cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY_INV,
                                    block_size,
                                    c)

    block_size, c = (41, 20)
    result3 = cv2.adaptiveThreshold(img,
                                    255,
                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV,
                                    block_size,
                                    c)

    result = cv2.add(result1, result2)
    result = cv2.add(result, result3)

    if mask is not None:
        result = cv2.bitwise_and(result, result, mask=mask)

    return result


def top_binarization_routine_hsv(image, hsv_min, hsv_max):
    """
    Binarization of top image for Lemnatech cabin based on hsv segmentation.
    """
    # ==========================================================================
    # Check Parameters
    if not isinstance(image, numpy.ndarray):
        raise TypeError('image should be a numpy.ndarray')

    if image.ndim != 3:
        raise ValueError('image should be 3D array')
    # ==========================================================================

    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    #   =======================================================================
    #   Main area segmentation
    main_area_seg = cv2.medianBlur(hsv_image, ksize=9)
    main_area_seg = cv2.inRange(main_area_seg, hsv_min, hsv_max)

    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    main_area_seg = cv2.dilate(main_area_seg, element, iterations=5)
    main_area_seg = cv2.erode(main_area_seg, element, iterations=5)

    return main_area_seg

# ==============================================================================

#deprecated
def side_binarization_hsv(image, factor):
    """
    Binarization of side image for Lemnatech cabin based on hsv segmentation.

    Based on Michael pipeline
    """
    # elementMorph = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    # ==========================================================================
    # Check Parameters
    if not isinstance(image, numpy.ndarray):
        raise TypeError('image should be a numpy.ndarray')
    if not isinstance(factor, BinarizationFactor):
        raise TypeError('factor should be a BinarizationFactor object')

    if image.ndim != 3:
        raise ValueError('image should be 3D array')
    # ==========================================================================

    c = factor.side_cubicle_domain
    image_cropped = image[c[0]:c[1], c[2]:c[3]]
    hsv_image = cv2.cvtColor(image_cropped, cv2.COLOR_BGR2HSV)

    #   =======================================================================
    #   Main area segmentation
    main_area_seg = cv2.medianBlur(hsv_image, ksize=9)
    main_area_seg = cv2.inRange(main_area_seg,
                                factor.side_roi_main.hsv_min,
                                factor.side_roi_main.hsv_max)

    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    main_area_seg = cv2.dilate(main_area_seg, element, iterations=2)
    main_area_seg = cv2.erode(main_area_seg, element, iterations=2)

    mask_cropped = factor.side_roi_main.mask[c[0]:c[1], c[2]:c[3]]
    main_area_seg = cv2.bitwise_and(main_area_seg,
                                    main_area_seg,
                                    mask=mask_cropped)

    #   =======================================================================
    #   Band area segmentation
    background_cropped = factor.side_cubicle_background[c[0]:c[1], c[2]:c[3]]
    hsv_background = cv2.cvtColor(background_cropped, cv2.COLOR_BGR2HSV)
    grayscale_background = hsv_background[:, :, 0]

    grayscale_image = hsv_image[:, :, 0]

    band_area_seg = cv2.subtract(grayscale_image, grayscale_background)
    retval, band_area_seg = cv2.threshold(band_area_seg,
                                          122,
                                          255,
                                          cv2.THRESH_BINARY)

    mask_cropped = factor.side_roi_orange_band.mask[c[0]:c[1], c[2]:c[3]]
    band_area_seg = cv2.bitwise_and(band_area_seg,
                                    band_area_seg,
                                    mask=mask_cropped)

    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    band_area_seg = cv2.dilate(band_area_seg, element, iterations=5)
    band_area_seg = cv2.erode(band_area_seg, element, iterations=5)

    #   =======================================================================
    #   Pot area segmentation
    pot_area_seg = cv2.inRange(hsv_image,
                               factor.side_roi_pot.hsv_min,
                               factor.side_roi_pot.hsv_max)

    mask_cropped = factor.side_roi_pot.mask[c[0]:c[1], c[2]:c[3]]
    pot_area_seg = cv2.bitwise_and(pot_area_seg,
                                   pot_area_seg,
                                   mask=mask_cropped)

    #   =======================================================================
    #   Full segmented image
    image_seg = cv2.add(main_area_seg, band_area_seg)
    image_seg = cv2.add(image_seg, pot_area_seg)

    image_out = numpy.zeros([image.shape[0], image.shape[1]], 'uint8')
    image_out[c[0]:c[1], c[2]:c[3]] = image_seg

    return image_out

#deprecated
def side_binarization_mean_shift(image, mean_image, factor):
    # ==========================================================================
    # Check Parameters
    if not isinstance(image, numpy.ndarray):
        raise TypeError('image should be a numpy.ndarray')
    if not isinstance(mean_image, numpy.ndarray):
        raise TypeError('mean_image should be a numpy.ndarray')
    if not isinstance(factor, BinarizationFactor):
        raise TypeError('factor should be a BinarizationFactor object')

    if image.ndim != 3:
        raise ValueError('image should be 3D array')
    if mean_image.ndim != 3:
        raise ValueError('mean_image should be 3D array')
    if image.shape != mean_image.shape:
        raise ValueError('image and mean_image should have the same shape')
    # ==========================================================================
    mask = cv2.add(factor.side_roi_main.mask,
                   factor.side_roi_orange_band.mask)
    
    mask = cv2.add(mask, factor.side_roi_panel.mask)

    binary_hsv_image = hsv_binarization(image,
                                        factor.side_roi_main.hsv_min,
                                        factor.side_roi_main.hsv_max,
                                        factor.side_roi_main.mask)

    binary_mean_shift_image = mean_shift_binarization(
        image,
        mean_image,
        float(factor.mean_shift_binarization_factor.threshold),
        factor.mean_shift_binarization_factor.dark_background,
        mask)

    result = cv2.add(binary_hsv_image, binary_mean_shift_image * 255)

    mask_clean_noise = cv2.add(factor.side_roi_orange_band.mask,
                               factor.side_roi_panel.mask)

    result = alinea.phenomenal.binarization_post_processing.clean_noise(
        result, mask_clean_noise)
    
    return result

#deprecated
def side_binarization_elcom(image, mean_image, factor):
    # ==========================================================================
    # Check Parameters
    if not isinstance(image, numpy.ndarray):
        raise TypeError('image should be a numpy.ndarray')
    if not isinstance(mean_image, numpy.ndarray):
        raise TypeError('mean_image should be a numpy.ndarray')
    if not isinstance(factor, BinarizationFactor):
        raise TypeError('factor should be a BinarizationFactor object')

    if image.ndim != 3:
        raise ValueError('image should be 3D array')
    if mean_image.ndim != 3:
        raise ValueError('mean_image should be 3D array')
    if image.shape != mean_image.shape:
        raise ValueError('image and mean_image should have the same shape')
    # ==========================================================================

    binary_hsv_image = hsv_binarization(image,
                                        factor.side_roi_stem.hsv_min,
                                        factor.side_roi_stem.hsv_max,
                                        factor.side_roi_stem.mask)

    binary_mean_shift_image = mean_shift_binarization(
        image,
        mean_image,
        float(factor.mean_shift_binarization_factor.threshold),
        factor.mean_shift_binarization_factor.dark_background,
        factor.side_roi_main.mask)

    result = cv2.add(binary_hsv_image, binary_mean_shift_image * 255)

    result = cv2.medianBlur(result, 3)
    
    return result

#deprecated
def top_binarization_hsv(image, factor):
    """
    Binarization of top image for Lemnatech cabin based on hsv segmentation.
    """
    # ==========================================================================
    # Check Parameters
    if not isinstance(image, numpy.ndarray):
        raise TypeError('image should be a numpy.ndarray')
    if not isinstance(factor, BinarizationFactor):
        raise TypeError('factor should be a BinarizationFactor object')

    if image.ndim != 3:
        raise ValueError('image should be 3D array')
    # ==========================================================================

    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    #   =======================================================================
    #   Main area segmentation
    main_area_seg = cv2.medianBlur(hsv_image, ksize=9)
    main_area_seg = cv2.inRange(main_area_seg,
                                factor.top_roi_main.hsv_min,
                                factor.top_roi_main.hsv_max)

    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    main_area_seg = cv2.dilate(main_area_seg, element, iterations=5)
    main_area_seg = cv2.erode(main_area_seg, element, iterations=5)

    return main_area_seg


# ==============================================================================


def top_binarization_elcom(bgr, factor, emptiesTop, useEmpty=True):
    # TODO Write test and documentation of tis function

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    luv = cv2.cvtColor(bgr, cv2.COLOR_BGR2LUV)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    hls = cv2.cvtColor(bgr, cv2.COLOR_BGR2HLS)
    xyz = cv2.cvtColor(bgr, cv2.COLOR_BGR2XYZ)
    yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)

    mask_pot = factor.top_cubicle.mask_pot
    mask_rails = factor.top_cubicle.mask_rails

    if factor.General.cabin == 5:
        if useEmpty:
            emptyImg = emptiesTop[0]
        imageBinSeuil = numpy.uint8( \
                    numpy.bitwise_or( \
                        numpy.bitwise_and( lab[:,:,1]>=120.5, \
                            numpy.bitwise_or( \
                                numpy.bitwise_and(lab[:,:,2]<139.5, \
                                    numpy.bitwise_or( \
                                        numpy.bitwise_and(lab[:,:,1]>=122.5, \
                                            numpy.bitwise_and(lab[:,:,1]<123.5, \
                                                numpy.bitwise_and(bgr[:,:,0] < 91.5, \
                                                    numpy.bitwise_and(hsv[:,:,1] >= 28.5, \
                                                        numpy.bitwise_and(yuv[:,:,0] >= 52.5, \
                                                            numpy.bitwise_or(luv[:,:,1] < 94.5, \
                                                                numpy.bitwise_and(luv[:,:,1] >= 94.5, bgr[:,:,2]>= 82.5) \
                                                            ) \
                                                        ) \
                                                    ) \
                                                ) \
                                            ) \
                                        ),
                                        numpy.bitwise_and(lab[:,:,1]<122.5, \
                                            numpy.bitwise_or(xyz[:,:,2] < 103.5, \
                                                numpy.bitwise_and(xyz[:,:,2] >= 103.5, \
                                                    numpy.bitwise_and(xyz[:,:,2] < 114.5, lab[:,:,1] < 121.5) \
                                                ) \
                                            ) \
                                        ) \
                                    ) \
                                ), \
                                numpy.bitwise_and(lab[:,:,2]>=139.5, \
                                    numpy.bitwise_or( \
                                        numpy.bitwise_and(hsv[:,:,1] < 55.5, \
                                            numpy.bitwise_and(bgr[:,:,0] < 143.5, bgr[:,:,2] < 110.5) \
                                        ), \
                                        numpy.bitwise_and(hsv[:,:,1] >= 55.5, \
                                            numpy.bitwise_and(xyz[:,:,2]>=56.5, \
                                                numpy.bitwise_or( \
                                                    numpy.bitwise_and(hsv[:,:,1]< 69.5, \
                                                        numpy.bitwise_or(hsv[:,:,0] >= 32.5, \
                                                            numpy.bitwise_and(hsv[:,:,0] < 32.5, \
                                                                numpy.bitwise_and(hsv[:,:,1]>= 61.5, \
                                                                    numpy.bitwise_or(numpy.bitwise_and(hsv[:,:,0] <= 20.5, xyz[:,:,2] < 138.5), \
                                                                        numpy.bitwise_and(hsv[:,:,0] < 20.5, \
                                                                            numpy.bitwise_or(lab[:,:,1] < 121.5, \
                                                                                numpy.bitwise_and(lab[:,:,1] >= 121.5, \
                                                                                    numpy.bitwise_or(luv[:,:,1] < 97.5, \
                                                                                        numpy.bitwise_and(luv[:,:,1] >= 97.5, \
                                                                                            numpy.bitwise_and(yuv[:,:,1] >= 134.5, yuv[:,:,1] < 137.5) \
                                                                                        ) \
                                                                                    ) \
                                                                                ) \
                                                                            ) \
                                                                        ) \
                                                                    ) \
                                                                ) \
                                                            ) \
                                                        ) \
                                                    ), \
                                                    numpy.bitwise_and(hsv[:,:,1]>= 69.5, \
                                                        numpy.bitwise_or( \
                                                            numpy.bitwise_and(bgr[:,:,1] < 84.5, \
                                                                numpy.bitwise_or(yuv[:,:,1] < 129.5, yuv[:,:,1] >= 135.5) \
                                                            ), \
                                                            numpy.bitwise_and(bgr[:,:,1] >= 84.5, \
                                                                numpy.bitwise_or( \
                                                                    numpy.bitwise_and(hsv[:,:,1] < 85.5, yuv[:,:,1]<143.5), \
                                                                    numpy.bitwise_and(hsv[:,:,1] >= 85.5, lab[:,:,1]<151.5) \
                                                                ) \
                                                            ) \
                                                        ) \
                                                    ) \
                                                ) \
                                            ) \
                                        ) \
                                    ) \
                                ) \
                            ) \
                        ), \
                        numpy.bitwise_and( lab[:,:,1]<120.5, \
                            numpy.bitwise_or( bgr[:,:,0] < 127.5, \
                                numpy.bitwise_and(bgr[:,:,0] >= 127.5, \
                                    numpy.bitwise_and(hsv[:,:,1] >= 49.5, yuv[:,:,1]<205.5) \
                                ) \
                            ) \
                        ) \
                    ) * 255)
        
    elif factor.General.cabin == 6:
        if useEmpty:
            emptyImg = emptiesTop[1]
        imageBinSeuil = numpy.uint8( \
                numpy.bitwise_or( \
                    numpy.bitwise_and( lab[:,:,1] >= 121.5, \
                        numpy.bitwise_or( \
                            numpy.bitwise_and( lab[:,:,2] < 146.5, \
                                numpy.bitwise_or( \
                                    numpy.bitwise_and( lab[:,:,1] >= 122.5, \
                                        numpy.bitwise_or( \
                                            numpy.bitwise_and( luv[:,:,1] >= 94.5, \
                                                numpy.bitwise_and( hsv[:,:,1] >= 38.5, \
                                                    numpy.bitwise_or( \
                                                        numpy.bitwise_and( lab[:,:,1] >= 124.5, \
                                                            numpy.bitwise_and( luv[:,:,2] >= 143.5, \
                                                                numpy.bitwise_and( hsv[:,:,1] >= 57.5, \
                                                                    numpy.bitwise_and( hsv[:,:,0] >= 22.5, yuv[:,:,2] < 116.5) \
                                                                ) \
                                                            ) \
                                                        ), \
                                                        numpy.bitwise_and(lab[:,:,1] < 124.5, \
                                                            numpy.bitwise_and( bgr[:,:,0] < 119.5, \
                                                                numpy.bitwise_or( \
                                                                    numpy.bitwise_and( hsv[:,:,1] < 47.5, \
                                                                        numpy.bitwise_and( lab[:,:,1] < 123.5, bgr[:,:,0] < 103.5) \
                                                                    ), \
                                                                    numpy.bitwise_and( hsv[:,:,1] >= 47.5, bgr[:,:,1] >= 56.5) \
                                                                ) \
                                                            ) \
                                                        ) \
                                                    ) \
                                                ) \
                                            ), \
                                            numpy.bitwise_and( luv[:,:,1] < 94.5, \
                                                numpy.bitwise_and( bgr[:,:,0] < 110.5, \
                                                    numpy.bitwise_and( lab[:,:,1] < 123.5, \
                                                        numpy.bitwise_or( numpy.bitwise_and( bgr[:,:,0] < 63.5, bgr[:,:,1] >= 56.5), \
                                                            numpy.bitwise_and( bgr[:,:,0] >= 63.5, \
                                                                numpy.bitwise_and(xyz[:,:,0] < 96.5, \
                                                                    numpy.bitwise_or( luv[:,:,2] >= 143.5, \
                                                                        numpy.bitwise_and( luv[:,:,2] < 143.5, \
                                                                            numpy.bitwise_and( luv[:,:,1] < 93.5, bgr[:,:,0] < 93.5) \
                                                                        ) \
                                                                    ) \
                                                                ) \
                                                            ) \
                                                        ) \
                                                    ) \
                                                ) \
                                            ) \
                                        ) \
                                    ), \
                                    numpy.bitwise_and( lab[:,:,1] < 122.5, \
                                        numpy.bitwise_or( \
                                            numpy.bitwise_and(bgr[:,:,0] >= 112.5, \
                                                numpy.bitwise_and(hsv[:,:,1] >= 48.5, bgr[:,:,0] < 130.5)\
                                            ), \
                                            numpy.bitwise_or(bgr[:,:,0] < 98.5, \
                                                numpy.bitwise_and( bgr[:,:,0] < 112.5, \
                                                    numpy.bitwise_or( hsv[:,:,1] >= 38.5, \
                                                        numpy.bitwise_and( hsv[:,:,1] < 38.5, \
                                                            numpy.bitwise_and( bgr[:,:,0] < 105.5, hsv[:,:,0] < 73.5) \
                                                        ) \
                                                    ) \
                                                ) \
                                            ) \
                                        ) \
                                    ) \
                                ) \
                            ), \
                            numpy.bitwise_and( lab[:,:,2] >= 146.5, bgr[:,:,0] < 161.5) \
                        ) \
                    ), \
                    numpy.bitwise_and( lab[:,:,1] < 121.5, \
                        numpy.bitwise_or( \
                            numpy.bitwise_and( bgr[:,:,0] >= 126.5, \
                                numpy.bitwise_and( hsv[:,:,1] >= 49.5, \
                                    numpy.bitwise_or( \
                                        numpy.bitwise_and( hsv[:,:,1] < 56.5, \
                                            numpy.bitwise_and( bgr[:,:,0] < 165.5, \
                                                numpy.bitwise_or( luv[:,:,2] >= 163.5, \
                                                    numpy.bitwise_and( luv[:,:,2] < 163.5, xyz[:,:,0] >= 157.5) \
                                                ) \
                                            ) \
                                        ), \
                                        numpy.bitwise_and( hsv[:,:,1] >= 56.5, bgr[:,:,0] < 169.5) \
                                    ) \
                                ) \
                            ), \
                            numpy.bitwise_or( bgr[:,:,0] < 108.5, \
                                numpy.bitwise_and( bgr[:,:,0] < 126.5, \
                                    numpy.bitwise_and( bgr[:,:,0] >= 108.5, \
                                        numpy.bitwise_or (hsv[:,:,1] >= 53.5, \
                                            numpy.bitwise_and( hsv[:,:,1] < 53.5, \
                                                numpy.bitwise_and( luv[:,:,2] >= 146.5, \
                                                    numpy.bitwise_or(bgr[:,:,0] < 116.5, \
                                                        numpy.bitwise_and( bgr[:,:,0] >= 116.5, hsv[:,:,1] >= 35.5) \
                                                    ) \
                                                ) \
                                            ) \
                                        ) \
                                    ) \
                                ) \
                            ) \
                        ) \
                    ) \
                ) * 255)
        
    else:
        imageBinSeuil = numpy.zeros(bgr.shape[0,2], 'uint8')
        emptyImg = numpy.zeros(bgr.shape, 'uint8')
        mask_pot = numpy.zeros(bgr.shape[0,2], 'uint8')
        mask_rails = numpy.zeros(bgr.shape[0,2], 'uint8')

    mask = numpy.bitwise_or(mask_pot, mask_rails)
    imageBinSeuilPot = numpy.bitwise_and(imageBinSeuil, mask)
    imageBinSeuilPot = ocv2.open(imageBinSeuilPot, iterations=3)

    if useEmpty:
        imageBinDiff = alinea.phenomenal.binarization_algorithm.mean_shift_binarization(bgr, emptyImg)*255
        imageBinDiff = numpy.bitwise_and(numpy.bitwise_and(imageBinDiff, imageBinSeuil), numpy.bitwise_not(mask))
    else:
        imageBinDiff = numpy.zeros(mask.shape, "uint8")

    return numpy.bitwise_or(imageBinSeuilPot, imageBinDiff)
