"""
Classes related to parsing annotation files for image datasets.

Copyright (c) 2021, Aaron Smith. All rights reserved.
"""

import csv
import xml.etree.ElementTree as xml_parser
from PIL import Image
import logging

from .annotations import ImageAnnotation, ObjectAnnotation
from .utils import find_image_filename


########################################################################################################################

class AnnotationFileParser:
    """
    Base class for objects that parse an annotation file and invoke a listener for each annotated image. The listener
    must accept two (2) variables: (1) a single ImageAnnotation instance; and (2) an array of ObjectAnnotation
    instances. The listener(s) is registered during instantiation as an array of 'image_annotation_listeners'.
    """

    def __init__(self, image_annotation_listeners):
        """
        Capture any references.

        :param image_annotation_listeners: array of listener functions to be invoked for each annotated image.
        """
        self.image_annotation_listeners = image_annotation_listeners
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, annotation_filename):
        """
        Parse the annotation file and invoke the ImageProcessor for each annotated image.

        :param annotation_filename: the name of the annotation file to parse.
        """
        pass


########################################################################################################################

class CvatAnnotationFileParser(AnnotationFileParser):
    """
    Specialisation of the AnnotationFileParser for parsing CVAT annotation files.
    """

    def __init__(self, image_annotation_listeners, image_dict):
        super().__init__(image_annotation_listeners=image_annotation_listeners)
        self.image_dict = image_dict

    def parse(self, annotation_filename):
        self.logger.debug(f'annotation_filename: {annotation_filename}')
        self.logger.debug(f'image_dict.size: {len(self.image_dict)}')
        xml_tree = xml_parser.parse(annotation_filename)
        root_node = xml_tree.getroot()
        image_count = 0
        for image_node in root_node.findall('./image'):
            image_count += 1
            image_filename = find_image_filename(self.image_dict, image_node.attrib['name'])
            image_width = int(image_node.attrib['width'])
            image_height = int(image_node.attrib['height'])
            image_annotation = ImageAnnotation(image_filename, image_width, image_height)

            object_annotations = []
            for box_node in image_node.findall('./box'):
                object_annotations.append(ObjectAnnotation(box_node.attrib['label'],
                                                           float(box_node.attrib['xtl']),
                                                           float(box_node.attrib['xbr']),
                                                           float(box_node.attrib['ytl']),
                                                           float(box_node.attrib['ybr'])))

            for image_annotation_listener in self.image_annotation_listeners:
                image_annotation_listener(image_annotation, object_annotations)

        self.logger.debug(f'{image_count} images parsed.')


########################################################################################################################

class CatlinSeaviewSurveyCsvAnnotationFileParser(AnnotationFileParser):
    """
    Specialisation of the AnnotationFileParser for parsing the Catlin Seaview Survey CSV-based annotation files.
    """

    def __init__(self, image_annotation_listeners, image_dict, image_patch_height, image_patch_width,
                 dataset_filter=None):
        super().__init__(image_annotation_listeners=image_annotation_listeners)
        self.image_dict = image_dict
        self.image_patch_height = image_patch_height
        self.image_patch_width = image_patch_width
        self.dataset_filter = dataset_filter

    def parse(self, annotation_filename):
        self.logger.debug(f'annotation_filename: {annotation_filename}')
        self.logger.debug(f'image_dict.size: {len(self.image_dict)}')
        csv_reader = csv.reader(open(annotation_filename), delimiter=',')
        row_count = 0
        current_file_id = None
        image_annotation = None
        object_annotations = []
        image_count = 0
        for row in csv_reader:
            if row_count % 1000 == 0:
                self.logger.debug(f'rows processed: {row_count}')

            # Ignore the header row.
            if row_count > 0:
                file_id = row[0]
                short_filename = row[0] + '.jpg'
                y = int(row[1])
                x = int(row[2])
                label_name = row[3]
                label = row[4]
                func_group = row[5]
                dataset = row[7]

                # If a dataset filter has been specified, ignore any records that do not match.
                if self.dataset_filter is None or self.dataset_filter == dataset:

                    # Check if the image has changed.
                    if not file_id == current_file_id:

                        # A different image is being annotated, so pass the current annotations to the processor.
                        if len(object_annotations) > 0:

                            for image_annotation_listener in self.image_annotation_listeners:
                                image_annotation_listener(image_annotation, object_annotations)

                        # Start handling the new image.
                        image_count += 1
                        current_file_id = file_id
                        image_filename = self.image_dict[short_filename]
                        image = Image.open(image_filename)
                        image_width, image_height = image.size
                        image_annotation = ImageAnnotation(image_filename=image_filename,
                                                           image_width=image_width,
                                                           image_height=image_height)
                        object_annotations = []

                    # Capture the object annotations.
                    xmin = x - self.image_patch_width // 2
                    xmax = x + self.image_patch_width // 2
                    ymin = y - self.image_patch_height // 2
                    ymax = y + self.image_patch_height // 2

                    # Cache the object annotations if they fit entirely within the image.
                    if xmin > 0 \
                            and xmax < image_annotation.image_width \
                            and ymin > 0 \
                            and ymax < image_annotation.image_height:
                        object_annotations.append(ObjectAnnotation(class_id=label,
                                                                   xmin=xmin,
                                                                   xmax=xmax,
                                                                   ymin=ymin,
                                                                   ymax=ymax))

            row_count += 1

        self.logger.debug(f'{image_count} images parsed.')
