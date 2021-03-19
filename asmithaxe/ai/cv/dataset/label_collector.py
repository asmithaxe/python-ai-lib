"""
Classes related to collecting a list of labels, and providing searching and persistence services.

Copyright (c) 2021, Aaron Smith. All rights reserved.
"""

import logging
import os

from .annotation_parser import AnnotationListener
from .pipeline import PipelineStateListener

class LabelCollector(AnnotationListener, PipelineStateListener):
    """
    Base class that performs the function of collecting labels, and providing searching services. Specialisations of
    this class provide additional services, such as persistence services.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Keep track of the unique labels.
        self.unique_labels = {}

    def on_annotation_available(self, image_annotation, object_annotations):
        """
        Checks for any new labels and add them to the list.

        :param label: the label to cache.
        """

        for object_annotation in object_annotations:
            label = object_annotation.label
            if label not in self.unique_labels:
                self.unique_labels[label] = len(self.unique_labels) + 1
                self.logger.debug(f'Adding "{label}"')

    def find(self, label):
        """
        Search the collection for the specified label.

        :param label: the search string
        :return: the position of the specified label within the collection.
        """
        return self.unique_labels[label] if label in self.unique_labels else None

    def get_num(self):
        """
        Returns the number of unique labels currently held by the collector.

        :return: the number of unique labels currently held by the collector.
        """
        return len(self.unique_labels)


########################################################################################################################

class LabelMapLabelCollector(LabelCollector):
    """
    Specialisation of the LabelCollector that persists the list of unique labels as a LabelMap file.
    """

    def __init__(self, filename):
        super().__init__()

        # Cache the filename.
        self.filename = filename

        # Ensure the location exists.
        path = os.path.split(self.filename)[0]
        if not os.path.exists(path):
            os.makedirs(path)

    def on_pipeline_stop(self):
        file = open(self.filename, 'w')
        for label in self.unique_labels:
            file.write('item {\n')
            file.write('id: ' + str(self.unique_labels[label]) + '\n')
            file.write('name: \'' + label + '\'\n')
            file.write('}\n')
