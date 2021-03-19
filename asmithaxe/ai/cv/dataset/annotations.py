"""
Value objects related to image dataset annotations.

Copyright (c) 2021, Aaron Smith. All rights reserved.
"""


class ImageAnnotation:
    """
    Value object representing the annotation of a single image.
    """

    def __init__(self, image_filename, image_width, image_height):
        self.image_filename = image_filename
        self.image_format = 'png' if image_filename.endswith('png') else 'jpg'
        self.image_width = image_width
        self.image_height = image_height


class ObjectAnnotation:
    """
    Value object representing the annotation of a single object within an annotated image.
    """

    def __init__(self, label, xmin, xmax, ymin, ymax):
        self.label = label
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
