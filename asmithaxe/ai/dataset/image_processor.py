"""
Classes related to processing/manipulating images in datasets.

Copyright (c) 2021, Aaron Smith. All rights reserved.
"""

from PIL import Image
import logging
import os
from object_detection.utils import visualization_utils as viz_utils

from .annotations import ImageAnnotation, ObjectAnnotation


class ImageLoader:
    """
    Helper class that loads the image specified by the ImageAnnotation and invokes an ImpactProcessor class for
    processing.
    """

    def __init__(self, image_processors):
        self.image_processors = image_processors
        self.logger = logging.getLogger(self.__class__.__name__)

    def load(self, image_annotation, object_annotations):
        self.logger.debug(f'{image_annotation.image_filename} -> {len(object_annotations)}')
        """
        If at least one ObjectAnnotation is specified, load the referenced image and invoke each of the registered
        processing implementations. These are methods with the signature:
        Image, ImageAnnotation, array of ObjectAnnotation.
        """
        if len(object_annotations) > 0:
            image = Image.open(image_annotation.image_filename)
            for image_processor in self.image_processors:
                image_processor(image, image_annotation, object_annotations)


########################################################################################################################

class ImageProcessor:
    """
    Base class for objects that perform a function on an image and then invokes the next ImageProcessor(s).
    """

    def __init__(self, image_processors):
        self.image_processors = image_processors
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(self, image, image_annotation, object_annotations):
        pass


########################################################################################################################

class CroppingImageProcessor(ImageProcessor):
    """
    Specialisation of the ImageProcessor that crops the annotated objects within the image to create a separate image
    for each object.
    """

    def __init__(self, image_processors, image_patch_height, image_patch_width):
        super().__init__(image_processors=image_processors)
        self.image_patch_height = image_patch_height
        self.image_patch_width = image_patch_width

    def process(self, image, image_annotation, object_annotations):
        split_filename = os.path.splitext(image_annotation.image_filename)
        filename_prefix = split_filename[0]
        filename_suffix = split_filename[1]
        crop_count = 0
        for object_annotation in object_annotations:

            # Verify that the patch area fits within the image, otherwise ignore the annotation.
            if object_annotation.xmin > self.image_patch_width // 2 and \
                    object_annotation.ymin > self.image_patch_height // 2 and \
                    object_annotation.xmax + self.image_patch_width // 2 < image_annotation.image_width and \
                    object_annotation.ymax + self.image_patch_height // 2 < image_annotation.image_height:
                # Calculate the cropping parameters.
                min_x = object_annotation.xmin - (self.image_patch_width // 2)
                max_x = object_annotation.xmax + (self.image_patch_width // 2)
                min_y = object_annotation.ymin - (self.image_patch_height // 2)
                max_y = object_annotation.ymin + (self.image_patch_height // 2)

                # Crop the image.
                cropped_image = image.crop((min_x, min_y, max_x, max_y))

                # Build the new ImageAnnotation and ObjectAnnotation for the cropped image.
                new_image_annotation = ImageAnnotation(
                    image_filename=filename_prefix + '_' + str(crop_count) + filename_suffix,
                    image_width=image_annotation.image_width,
                    image_height=image_annotation.image_height
                )
                new_object_annotation = ObjectAnnotation(class_id=object_annotation.class_id,
                                                         xmin=0,
                                                         xmax=self.image_patch_width,
                                                         ymin=0,
                                                         ymax=self.image_patch_height)

                # Invoke the next ImageProcessor(s).
                for image_processor in self.image_processors:
                    image_processor(cropped_image, new_image_annotation, [new_object_annotation])


########################################################################################################################

class AnnotationRenderingImageProcessor(ImageProcessor):
    """
    Specialisation of the ImageProcessor that renders the ObjectAnnotations on the image.
    """

    def process(self, image, image_annotation, object_annotations):
        for object_annotation in object_annotations:
            viz_utils.draw_bounding_box_on_image(image,
                                                 object_annotation.ymin,
                                                 object_annotation.xmin,
                                                 object_annotation.ymax,
                                                 object_annotation.xmax,
                                                 color='white',
                                                 thickness=1,
                                                 display_str_list=(object_annotation.class_id,),
                                                 use_normalized_coordinates=False)

        # Invoke the next ImageProcessor(s).
        for image_processor in self.image_processors:
            image_processor(image, image_annotation, object_annotations)
