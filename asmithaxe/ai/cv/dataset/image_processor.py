"""
Classes related to processing/manipulating images in datasets.

Copyright (c) 2021, Aaron Smith. All rights reserved.
"""

from PIL import Image
import logging
import os
from object_detection.utils import visualization_utils as viz_utils

from .annotation_parser import AnnotationListener
from .annotations import ImageAnnotation, ObjectAnnotation

########################################################################################################################

class AnnotatedImageListener:
    """
    Interface for classes that want to be notified when an annotated image is available for processing.
    """

    def on_annotated_image_available(self, image, image_annotation, object_annotations):
        """
        Invoked when an annotated image is available for processing.
        """
    pass

########################################################################################################################

class ImageLoader(AnnotationListener):
    """
    Helper class that loads the image specified by the ImageAnnotation and invokes an ImpactProcessor class for
    processing.
    """

    def __init__(self, annotated_image_listeners):
        self.annotated_image_listeners = annotated_image_listeners
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_annotation_available(self, image_annotation, object_annotations):
        self.logger.debug(f'{image_annotation.image_filename} -> {len(object_annotations)}')
        """
        If at least one ObjectAnnotation is specified, load the referenced image and invoke each of the registered
        processing implementations. These are methods with the signature:
        Image, ImageAnnotation, array of ObjectAnnotation.
        """
        if len(object_annotations) > 0:
            image = Image.open(image_annotation.image_filename)
            for listener in self.annotated_image_listeners:
                listener.on_annotated_image_available(image, image_annotation, object_annotations)


########################################################################################################################

class ImageProcessor(AnnotatedImageListener):
    """
    Base class for objects that perform a function on an image and then invokes the next ImageProcessor(s).
    """

    def __init__(self, annotated_image_listeners):
        self.annotated_image_listeners = annotated_image_listeners
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_annotated_image_available(self, image, image_annotation, object_annotations):
        pass


########################################################################################################################

class CroppingImageProcessor(ImageProcessor):
    """
    Specialisation of the ImageProcessor that crops the annotated objects within the image to create a separate image
    for each object.
    """

    def on_annotated_image_available(self, image, image_annotation, object_annotations):
        split_filename = os.path.splitext(image_annotation.image_filename)
        filename_prefix = split_filename[0]
        filename_suffix = split_filename[1]
        crop_count = 0
        for object_annotation in object_annotations:

            # Crop the image.
            cropped_image = image.crop((object_annotation.xmin, object_annotation.ymin, object_annotation.xmax,
                                        object_annotation.ymax))

            # Build the new ImageAnnotation and ObjectAnnotation for the cropped image.
            new_image_annotation = ImageAnnotation(
                image_filename=filename_prefix + '_' + str(crop_count) + filename_suffix,
                image_width=image_annotation.image_width,
                image_height=image_annotation.image_height
            )
            new_object_annotation = ObjectAnnotation(class_id=object_annotation.class_id,
                                                     xmin=0,
                                                     xmax=object_annotation.xmax - object_annotation.xmin,
                                                     ymin=0,
                                                     ymax=object_annotation.ymax - object_annotation.ymin)

            # Invoke the next ImageProcessor(s).
            for listener in self.annotated_image_listeners:
                listener.on_annotated_image_available(cropped_image, new_image_annotation, [new_object_annotation])

            # Increment the counter.
            crop_count += 1


########################################################################################################################

class AnnotationRenderingImageProcessor(ImageProcessor):
    """
    Specialisation of the ImageProcessor that renders the ObjectAnnotations on the image.
    """

    def on_annotated_image_available(self, image, image_annotation, object_annotations):
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
        for listener in self.annotated_image_listeners:
            listener.on_annotated_image_available(image, image_annotation, object_annotations)
