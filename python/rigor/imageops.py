"""
Various utilities for dealing with images
"""

from rigor.config import config

try:
	import Image
except ImportError:
	import PIL.Image as Image

import shutil
import tempfile
import os

def build_path(image, base_path, separator = os.sep):
	"""
	Given a base path, constructs a path to the image
	"""
	return os.extsep.join((separator.join((base_path, image['locator'][0:2], image['locator'][2:4], image['locator'])), image['format']))

def build_thumbnail_path(image, base_path, size, separator = os.sep):
	"""
	Given a base path, constructs a path to the image's thumbnail
	"""
	return os.extsep.join((separator.join((base_path, '{0}x{0}'.format(int(size)), image['locator'][0:2], image['locator'][2:4], image['locator'])), image['format']))

def find(image):
	"""
	Returns the location in the repository where this image can be found.
	"""
	return build_path(image, config.get('global', 'image_repository'))

def find_thumbnail(image, size):
	"""
	Given a base path, constructs a path to the image's thumbnail
	"""
	return build_thumbnail_path(image, config.get('thumbnail', 'image_repository'), size)

def fetch(image):
	"""
	Given an Image object, this method either fetches it from the repository and
	copies it to the local temporary directory, or just returns the source,
	depending on configuration.  File is returned as an open file object.  If it
	is a temporary file, it will be deleted when it goes out of scope.
	"""
	source = find(image)
	if config.getboolean('global', 'copy_local'):
		destination = tempfile.NamedTemporaryFile(prefix='rigor-tmp-', delete=True)
		shutil.copyfile(source, destination.name)
		return destination
	else:
		return open(source, 'rb')

def read(path):
	"""
	Returns a PIL image from reading a given path
	"""
	return Image.open(path)
