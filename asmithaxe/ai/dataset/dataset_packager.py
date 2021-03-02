"""
Classes related to packaging image datasets.

Copyright (c) 2021, Aaron Smith. All rights reserved.
"""

import io
import os
import tensorflow as tf
from object_detection.utils import dataset_util
import logging


class DatasetPackager:
    """
    Base class for objects that package an annotated image.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def append(self, image, image_annotation, object_annotations):
        pass

    def close(self):
        pass


class TensorFlowRecordDatasetPackager(DatasetPackager):
    """
    Specialisation of the DatasetPackager for packaging an annotated image in a TensorFlowRecord file.
    """

    def __init__(self, dataset_filename, labelmap_filename = None, normalise_bounding_boxes = True):
        """
        Capture the properties on instantiation.

        :param dataset_filename: the filename to use for the packaged dataset.
        :param labelmap_filename: the filename for the labelmap file.
        :param normalise_bounding_boxes: flag that determines if the bounding box values are to be normalised with
        height/width on not.
        """
        super().__init__()
        self.dataset_filename = dataset_filename
        self.labelmap_filename = labelmap_filename
        self.normalise_bounding_boxes = normalise_bounding_boxes
        self.dataset_writer = tf.io.TFRecordWriter(self.dataset_filename)
        self.unique_class_ids = {}
        self.image_count = 0

    def append(self, image, image_annotation, object_annotations):
        self.image_count += 1
        xmins = []
        xmaxs = []
        ymins = []
        ymaxs = []
        classes_text = []
        classes_id = []
        for object_annotation in object_annotations:
            class_id = object_annotation.class_id

            # Add the class to the list of unique class ids.
            if class_id not in self.unique_class_ids:
                self.unique_class_ids[class_id] = len(self.unique_class_ids) + 1

            # Transform the bounding box locations to fractions within the image size.
            xmins.append(
                object_annotation.xmin / image_annotation.image_width if self.normalise_bounding_boxes else object_annotation.xmin)
            xmaxs.append(
                object_annotation.xmax / image_annotation.image_width if self.normalise_bounding_boxes else object_annotation.xmax)
            ymins.append(
                object_annotation.ymin / image_annotation.image_height if self.normalise_bounding_boxes else object_annotation.ymin)
            ymaxs.append(
                object_annotation.ymax / image_annotation.image_height if self.normalise_bounding_boxes else object_annotation.ymax)
            classes_text.append(class_id.encode('utf8'))
            classes_id.append(self.unique_class_ids[class_id])

        # encoded_image = image.getData()
        imageBuf = io.BytesIO()
        image.save(imageBuf, format="JPEG")
        encoded_image = imageBuf.getvalue()
        tf_example = tf.train.Example(features=tf.train.Features(feature={
            'image/height': dataset_util.int64_feature(image_annotation.image_height),
            'image/width': dataset_util.int64_feature(image_annotation.image_width),
            'image/filename': dataset_util.bytes_feature(image_annotation.image_filename.encode('utf8')),
            'image/source_id': dataset_util.bytes_feature(image_annotation.image_filename.encode('utf8')),
            'image/encoded': dataset_util.bytes_feature(encoded_image),
            'image/format': dataset_util.bytes_feature(image_annotation.image_format.encode()),
            'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
            'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
            'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
            'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
            'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
            'image/object/class/label': dataset_util.int64_list_feature(classes_id),
        }))
        self.dataset_writer.write(tf_example.SerializeToString())

    def close(self):
        self.logger.debug(f'{self.image_count} images packaged.')
        # Close the dataset file.
        self.dataset_writer.close()

        # Write the LabelMap file.
        if self.labelmap_filename is not None:
            label_file = open(self.labelmap_filename, 'w')
            for label in self.unique_class_ids:
                label_file.write('item {\n')
                label_file.write('id: ' + str(self.unique_class_ids[label]) + '\n')
                label_file.write('name: \'' + label + '\'\n')
                label_file.write('}\n')


########################################################################################################################

class StoreByFullFilenameDatasetPackager(DatasetPackager):
    """
    Specialisation of the DatasetPackager that saves the image using the full filename in the ImageAnnotation object.
    """

    def __init__(self, output_path):
        """
        Capture the properties on instantiation.

        :param output_path: the root path for the output file structure.
        """
        super().__init__()
        self.output_path = output_path
        self.image_count = 0

    def append(self, image, image_annotation, object_annotations):
        image.copy().save(os.path.join(self.output_path, image_annotation.image_filename))
        self.image_count += 1

    def close(self):
        self.logger.debug(f'{self.image_count} images stored.')


########################################################################################################################

class StoreByShortFilenameDatasetPackager(DatasetPackager):
    """
    Specialisation of the DatasetPackager that saves the image using the short filename in the ImageAnnotation object.
    """

    def __init__(self, output_path):
        """
        Capture the properties on instantiation.

        :param output_path: the root path for the output file structure.
        """
        super().__init__()
        self.output_path = output_path
        self.image_count = 0

    def append(self, image, image_annotation, object_annotations):
        image.save(os.path.join(self.output_path, os.path.basename(image_annotation.image_filename)))
        self.image_count += 1

    def close(self):
        self.logger.debug(f'{self.image_count} images stored.')


########################################################################################################################

class StoreByLabelDatasetPackager(DatasetPackager):
    """
    Specialisation of the DatasetPackager that saves the image using the short filename in the ImageAnnotation object
    in a sub-directory based on the label of the first ObjectAnnotation.
    """

    def __init__(self, output_path):
        """
        Capture the properties on instantiation.

        :param output_path: the root path for the output file structure.
        """
        super().__init__()
        self.output_path = output_path
        self.image_count = 0

    def append(self, image, image_annotation, object_annotations):

        if len(object_annotations) > 0:
            object_annotation = object_annotations[0]
            _output_path = os.path.join(self.output_path, object_annotation.class_id)
            if not os.path.exists(_output_path):
                os.makedirs(_output_path)
            image.save(os.path.join(_output_path, os.path.basename(image_annotation.image_filename)))
            self.image_count += 1

    def close(self):
        self.logger.debug(f'{self.image_count} images packaged.')
