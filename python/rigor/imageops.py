"""
Various utilities for dealing with images
"""

from rigor.config import config
from rigor.dbmapper import DatabaseMapper

try:
	import cv2
	import numpy as np
	kImageReadFlags = cv2.CV_LOAD_IMAGE_UNCHANGED
except ImportError:
	pass

import shutil
import tempfile
import urlparse
import urllib2
import urllib
import contextlib
import os

def build_path(image):
	""" Constructs a relative path to the image """
	return os.path.join(image['locator'][0:2], image['locator'][2:4], os.extsep.join((image['locator'], image['format'])))

def build_thumbnail_path(image, size):
	""" Constructs a full path for the image's thumbnail.  """
	return os.path.join('{0}x{0}'.format(int(size)), build_path(image))

def find(image, force_url=False):
	"""
	Returns the location in the repository where this image can be found. If
	force_url is True, the path will be returned as a URL even if it's local.
	"""
	path = os.path.join(config.get('global', 'image_repository'), build_path(image))
	if force_url:
		parsed = urlparse.urlparse(path)
		if not parsed.scheme:
			return 'file://' + os.path.abspath(parsed.path)
	return path

def find_thumbnail(image, size):
	"""
	Given a base path, constructs a path to the image's thumbnail
	"""
	return os.path.join(config.get('thumbnail', 'image_repository'), build_thumbnail_path(image, size))

def fetch(image):
	"""
	Given an Image object, this will fetch it from the URL or repository base,
	and then read it into a numpy array.
	"""
	source = find(image, force_url=True)
	with contextlib.closing(urllib2.urlopen(source)) as image_data:
		image_array = np.frombuffer(image_data.read(), np.uint8)
	return cv2.imdecode(image_array, kImageReadFlags)

def read(path):
	"""
	Returns a numpy array from reading a given path
	"""
	return cv2.imread(path, kImageReadFlags)

def destroy_image(database, image):
	""" Removes an image and any thumbnails from disk and from the database """
	mapper = DatabaseMapper(database)
	with database.get_cursor() as cursor:
		mapper._delete_image(cursor, image) # pylint: disable=W0212
		image_path = find(image)
		os.unlink(image_path)
		for thumbnail_dir in os.listdir(config.get('thumbnail', 'image_repository')):
			image_thumbnail_path = build_path(image, os.path.join(config.get('thumbnail', 'image_repository'), thumbnail_dir))
			os.unlink(image_thumbnail_path)
