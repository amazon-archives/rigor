""" Various utilities for dealing with percept data """

from rigor.s3 import DefaultS3Client
from rigor.types import Percept

try:
	import cv2
	import numpy as np
	_kImageReadFlags = cv2.CV_LOAD_IMAGE_UNCHANGED
except ImportError:
	pass

from urlparse import urlsplit
import urllib2
import contextlib
import os

class PerceptOps(object):
	"""
	Various utilities for dealing with percept data

	:param config: configuration data
	:type config: :py:class:`~rigor.config.RigorConfiguration`
	"""

	def __init__(self, config):
		self._config = config

	def fetch(self, percept):
		"""
		Given a percept, this will fetch its data from the repository, returning it as an open file-like object with a :py:func:`contextlib.closing` wrapper

		:param dict percept: percept metadata
		:return: percept data
		:rtype: file
		"""
		return self.read(percept.locator, percept.credentials)

	def read(self, url, credentials=None):
		"""
		Reads data from the specified URL, returning it as an open file-like object with a :py:func:`contextlib.closing` wrapper

		:param str url: URL containing data
		:param str credentials: optional name of configuration section with S3 credentials
		"""
		parsed = urlsplit(url)
		if not parsed.netloc:
			return open(parsed.path, 'rb')
		if parsed.scheme == 's3':
			s3 = DefaultS3Client(self._config, parsed.netloc, credentials)
			data = s3.get(parsed.path)
		else:
			data = urllib2.urlopen(url)
		if data is None:
			return None
		return contextlib.closing(data)

	def remove(self, url, credentials=None):
		"""
		Removes percept data at the given path. Does not make any changes to the database; this is generally meant to be used by the :py:meth:`destroy` method, though it is available for other purposes.

		:param str url: URL for the location of the percept
		:param str credentials: optional name of configuration section with S3 credentials

		.. todo::

			Currently, only local and S3 files are supported.
		"""
		parsed = urlsplit(url)
		if not parsed.netloc:
			# Local file
			os.unlink(parsed.path)
		elif parsed.scheme == 's3':
			s3 = DefaultS3Client(self._config, parsed.netloc, credentials)
			s3.delete(parsed.path)
		else:
			raise NotImplementedError("Files not in a local repository or S3 bucket can't be deleted")

	def destroy(self, percept, session):
		"""
		Removes a percept from the database, and its data from the repository.

		:param percept: either a :py:class:`~rigor.types.Percept` object, or an integer identifier
		:param session: database session
		"""
		if not hasattr(percept, 'id'):
			percept = session.query(Percept).get(percept)
		session.delete(percept)
		self.remove(percept.locator, percept.credentials)

class ImageOps(PerceptOps):
	"""
	Utilities for dealing with image-type percepts

	:param config: configuration data
	:type config: :py:class:`~rigor.config.RigorConfiguration`
	"""

	def __init__(self, config):
		super(ImageOps, self).__init__(config)

	def fetch(self, percept):
		"""
		Given a percept, this will fetch its data from the URL or repository base,
		returning it as a NumPy array

		:param dict percept: Percept metadata
		:return: decoded bitmap
		:rtype: :py:class:`numpy.ndarray`
		"""
		with super(ImageOps, self).fetch(percept) as image_data:
			return ImageOps.decode(image_data)

	@staticmethod
	def decode(percept_data):
		"""
		Given an image, this will decode it and return it as a NumPy array.

		:param percept_data: image data or path to image file
		:type percept_data: either a file-like object, or a path to an image file
		:return: decoded bitmap
		:rtype: :py:class:`numpy.ndarray`
		"""
		if hasattr(percept_data, 'read'):
			image_array = np.frombuffer(percept_data.read(), np.uint8)
			return cv2.imdecode(image_array, _kImageReadFlags)
		return cv2.imread(percept_data, _kImageReadFlags)
