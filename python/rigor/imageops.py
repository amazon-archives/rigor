"""
Various utilities for dealing with images
"""

from rigor.config import config
from rigor.dbmapper import DatabaseMapper

try:
	import cv2
except ImportError:
	pass

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
	return build_path(image, os.path.join(base_path, '{0}x{0}'.format(int(size))), separator)

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
	depending on configuration.  It will be read as a numpy array and returned.
	"""
	source = find(image)
	if config.getboolean('global', 'copy_local'):
		with tempfile.NamedTemporaryFile(prefix='rigor-tmp-', delete=True) as destination:
			shutil.copyfile(source, destination.name)
			return read(destination.name)
	else:
		return read(source)

def read(path):
	"""
	Returns a numpy array from reading a given path
	"""
	return cv2.imread(path, -1) # Load image as-is, no color conversion

def destroy_image(database, image):
	""" Completely Removes an image from the database, along with its tags, annotations, and any anotation tags. Also deletes the image file from disk."""
	mapper = DatabaseMapper(database)
	with database.get_cursor() as cursor:
		sql = "DELETE FROM tag WHERE image_id = %s;"
		cursor.execute(sql, (image['id'],))
		annotations = mapper._get_annotations_by_image_id(cursor, image['id']) # pylint: disable=W0212
		for annotation in annotations:
			sql = "DELETE FROM annotation_tag WHERE annotation_id = %s"
			cursor.execute(sql, (annotation['id'],))
			mapper._delete_annotation(cursor, annotation['id']) # pylint: disable=W0212
		sql = "DELETE FROM image WHERE id = %s;"
		cursor.execute(sql, (image['id'],))
		image_path = find(image)
		os.unlink(image_path)
		for thumbnail_dir in os.listdir(config.get('thumbnail', 'image_repository')):
			image_thumbnail_path = build_path(image, os.path.join(config.get('thumbnail', 'image_repository'), thumbnail_dir))
			os.unlink(image_thumbnail_path)
