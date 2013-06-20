"""
Used for applying an algorithm to a single image
"""

import rigor.imageops

import abc
import time

class Algorithm(object):
	""" Abstract base class for running an algorithm against a test image """
	__metaclass__ = abc.ABCMeta

	def __init__(self):
		self._logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self._arguments = None

	def set_arguments(self, arguments):
		""" Makes command-line arguments available to the algorithm """
		self._arguments = arguments

	def prefetch(self, image): # pylint: disable=R0201
		"""
		This method can be overridden to alter or use image metadata before the
		image has been fetched from the data store.

		NOTE: Be sure to remember to return the metadata when you're done.
		"""
		return image

	def postfetch(self, _image, image_data): # pylint: disable=R0201
		"""
		This method can be overridden to alter or use the image's data or metadata
		once it has been fetched from the data store, but before the algorithm
		begins running.

		NOTE: Be sure to return the image data when you're done.
		"""
		return image_data

	@abc.abstractmethod
	def run(self, image_data):
		"""
		All Algorithm-based objects must implement this method.  This is where the
		actual algorithm runs on the supplied image_data.  Return any results.
		"""
		pass

	def parse_annotations(self, annotations): # pylint: disable=R0201
		"""
		This method can be used to change the format of annotations returned from the database to something easier to analyze in later steps.

		NOTE: Be sure to eturn the new annotations object when you're done.
		"""
		return annotations

	def apply(self, image):
		"""
		Sets up all of the operations performed for each image, starts a timer,
		runs the algorithm, and formats the results, annotations, etc. into a tuple
		for later evaluation.
		"""
		image = self.prefetch(image)
		image_data = rigor.imageops.fetch(image)
		image_data = self.postfetch(image, image_data)
		start_time = time.time()
		result = self.run(image_data)
		elapsed = time.time() - start_time
		annotations = self.parse_annotations(image['annotations'])
		if 'annotations' in image:
			del(image['annotations'])
		if 'tags' in image:
			del(image['tags'])
		return (image, result, annotations, elapsed)
