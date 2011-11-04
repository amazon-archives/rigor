"""
Various utilities for dealing with images
"""

from vision.config import config
from vision.model.image import Image
from vision.model.annotation import Annotation
from vision.objectmapper import ObjectMapper

import Image as PILImage

import shutil
import tempfile
import os

def fetch(image):
	"""
	Given an Image object, this method either fetches it from the repository and
	copies it to the local temporary directory, or just returns the source,
	depending on configuration.  File is returned as an open file object.  If it
	is a temporary file, it will be deleted when it goes out of scope.
	"""
	source = os.extsep.join((os.path.join(config.get('global', 'image_repository'), image.locator[0:2], image.locator[2:4], image.locator), image.format))
	if config.getboolean('global', 'copy_local'):
		destination = tempfile.NamedTemporaryFile(prefix='vision-tmp-', delete=True)
		shutil.copyfile(source, destination.name)
		return destination
	else:
		return open(source, 'rb')

def read(path):
	"""
	Returns a PIL image from reading a given path
	"""
	return PILImage.open(path)
