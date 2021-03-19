import os
import re


def build_image_dict(path):
    """
    Recursive function for building a dictionary of image files (jpg and png), mapping filename -> full path, from the
    root path specified. The function is recursively invoked for each sub-directory.

    Note: the function assumes that each filename is unique.

    :param path: the path from which to search for image files. Any directories found in the path will result in this
    function being recursively invoked.
    :return: dictionary of image files where the key is the unique filename, and the value is the full path name.
    """
    image_dict = {}
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        if (os.path.isdir(full_path)):
            image_dict.update(build_image_dict(full_path))
        else:
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                image_dict[filename] = full_path
    return image_dict


def find_image_filename(input_image_dict, filename):
    """
    Helper function to retrieve the full filename of the specified image using the provided dictionary.

    :param input_image_dict: the dictionary containing the full filename of available images.
    :param short_filename: the unique short filename of the image to use to look up the full filename in the dictionary.
    :return: the full image filename.
    """
    short_filename = filename if "/" not in filename else re.split("([^/]+$)", filename)[1]
    return input_image_dict[short_filename]


def build_image_list(path):
    """
    Recursive function for building a list of image files (jpg and png) for the path specified. The function is
    recursively invoked for each sub-directory.

    :param path: the path from which to search for image files. Any directories found in the path will result in this
    function being recursively invoked.
    :return: list of full path names of image files found.
    """
    image_list = []
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        if (os.path.isdir(full_path)):
            image_list.append(build_image_list(full_path))
        else:
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                image_list.append(full_path)
    return image_list
