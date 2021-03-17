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

    def __init__(self, image_annotation_listeners, label_collector=None):
        """
        Capture any references.

        :param image_annotation_listeners: array of listener functions to be invoked for each annotated image.
        :param label_collector: a label collector (if any) to collect the list of unique labels.
        """
        self.image_annotation_listeners = image_annotation_listeners
        self.label_collector = label_collector
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, annotation_filename):
        """
        Parse the annotation file and invoke the ImageProcessor for each annotated image.

        :param annotation_filename: the name of the annotation file to parse.
        """
        self.logger.debug(f'annotation_filename: {annotation_filename}')
        if self.label_collector is not None:
            self.label_collector.clear()


########################################################################################################################

class CvatAnnotationFileParser(AnnotationFileParser):
    """
    Specialisation of the AnnotationFileParser for parsing CVAT annotation files.
    """

    def __init__(self, image_annotation_listeners, image_dict, label_collector=None):
        super().__init__(image_annotation_listeners=image_annotation_listeners, label_collector=label_collector)
        self.image_dict = image_dict
        self.logger.debug(f'Available images: {len(self.image_dict)}')

    def parse(self, annotation_filename):
        super().parse(annotation_filename)
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
                label = box_node.attrib['label']
                if self.label_collector is not None:
                    self.label_collector.register(label)
                object_annotations.append(ObjectAnnotation(label,
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
                 dataset_filter=None, label_collector=None):
        super().__init__(image_annotation_listeners=image_annotation_listeners, label_collector=label_collector)
        self.image_dict = image_dict
        self.image_patch_height = image_patch_height
        self.image_patch_width = image_patch_width
        self.dataset_filter = dataset_filter

        # Dump configuration to debug logs.
        self.logger.debug(f'Available images: {len(self.image_dict)}')
        self.logger.debug(f'image_patch_height: {self.image_patch_height}')
        self.logger.debug(f'image_patch_width: {self.image_patch_width}')
        self.logger.debug(f'dataset_filter: {self.dataset_filter}')

    def parse(self, annotation_filename):
        super().parse(annotation_filename)

        # Build a map of annotations to each image.
        image_to_annotations_dict = {}
        csv_reader = csv.reader(open(annotation_filename), delimiter=',')
        for row in csv_reader:
            file_id = row[0]
            short_filename = row[0] + '.jpg'
            dataset = row[7]

            # Check if the image is available for processing, and the dataset filter matches (if set).
            if short_filename in self.image_dict and \
                    (self.dataset_filter is None or self.dataset_filter == dataset):

                y = int(row[1])
                x = int(row[2])
                label_name = row[3]
                label = row[4]
                func_group = row[5]

                if self.label_collector is not None:
                    self.label_collector.register(label)

                if not short_filename in image_to_annotations_dict:
                    image_to_annotations_dict[short_filename] = []
                annotations = image_to_annotations_dict[short_filename]
                annotations.append({
                    'file_id': file_id,
                    'short_filename': short_filename,
                    'x': x,
                    'y': y,
                    'label_name': label_name,
                    'label': label,
                    'func_group': func_group,
                    'dataset': dataset
                })

        # Process each image/annotation grouping.
        image_count = 0
        for short_filename in image_to_annotations_dict:
            annotations = image_to_annotations_dict[short_filename]
            image_count += 1

            # Populate the image annotation.
            image_filename = self.image_dict[short_filename]
            image = Image.open(image_filename)
            image_width, image_height = image.size
            image_annotation = ImageAnnotation(image_filename=image_filename,
                                               image_width=image_width,
                                               image_height=image_height)
            object_annotations = []
            for annotation in annotations:

                # Capture the object annotations.
                xmin = annotation['x'] - self.image_patch_width // 2
                xmax = annotation['x'] + self.image_patch_width // 2
                ymin = annotation['y'] - self.image_patch_height // 2
                ymax = annotation['y'] + self.image_patch_height // 2

                # Cache the object annotations if they fit entirely within the image.
                if xmin > 0 \
                        and xmax < image_annotation.image_width \
                        and ymin > 0 \
                        and ymax < image_annotation.image_height:
                    object_annotations.append(ObjectAnnotation(label=annotation['label'],
                                                               xmin=xmin,
                                                               xmax=xmax,
                                                               ymin=ymin,
                                                               ymax=ymax))

            # Trigger registered annotation listeners.
            if len(object_annotations) > 0:
                for image_annotation_listener in self.image_annotation_listeners:
                    image_annotation_listener(image_annotation, object_annotations)

        self.logger.debug(f'{image_count} images parsed.')
