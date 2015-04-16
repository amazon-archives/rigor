""" Used for applying an algorithm to a single percept """

import abc
import time
import rigor.logger
from rigor.perceptops import ImageOps

class Algorithm(object):
	"""
	Abstract base class for running an algorithm against a test percept
	"""
	__metaclass__ = abc.ABCMeta

	def __init__(self):
		self.logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self.parameters = None

	def set_parameters(self, parameters):
		""" Makes parameters, possibly from command-line arguments, available to the algorithm """
		self.parameters = parameters

	def prefetch(self, percept):
		"""
		This method can be overridden to alter or use percept metadata before the
		percept has been fetched from the data store.

		:param dict percept: percept metadata
		:return: percept metadata
		:rtype: dict

		.. NOTE::

			Be sure to return the metadata when you're done.
		"""
		return percept

	def postfetch(self, percept, percept_data):
		"""
		This method can be overridden to alter or use the percept's data or metadata
		once it has been fetched from the data store, but before the algorithm
		begins running.

		:param dict percept: percept metadata
		:param file percept_data: percept data
		:return: percept data
		:rtype: file

		.. NOTE::

			Be sure to return the data when you're done.
		"""
		return percept_data

	@abc.abstractmethod
	def run(self, percept_data):
		"""
		All :py:class:`Algorithm`-based objects must implement this method.  This is where the actual algorithm runs on the supplied data.

		:param file percept_data: percept data
		:return: results of the algorithm
		"""
		pass

	def parse_annotations(self, annotations):
		"""
		This method can be used to change the format of annotations returned from the database to something easier to analyze in later steps.

		:param dict annotations: annotations in their stored format
		:return: new annotations object

		.. NOTE::

			Be sure to return the new annotations object when you're done.
		"""
		return annotations

	def apply(self, percept, percept_data):
		"""
		Sets up all of the operations performed for each percept, starts a timer,
		runs the algorithm, and formats the results, annotations, etc. into a tuple
		for later evaluation.

		:param dict percept: percept metadata
		:param file percept_data: percept data
		"""
		percept_data = self.postfetch(percept, percept_data)
		start_time = time.time()
		result = self.run(percept_data)
		elapsed = time.time() - start_time
		annotations = self.parse_annotations(percept.annotations)
		return (percept.serialize(force_load=False), result, [annotation.serialize(force_load=False) for annotation in annotations], elapsed)

class ImageAlgorithm(Algorithm):
	"""
	Abstract base class for running an algorithm against a test percept, specialized for images
	"""
	def postfetch(self, percept, percept_data):
		"""
		This method can be overridden to alter or use the percept's data or metadata once it has been fetched from the data store, but before the algorithm begins running. If you override this method, be sure to call it before your implementation, as this is where OpenCV parses the image.

		:param dict percept: percept metadata
		:param file percept_data: percept data
		:return: percept data
		:rtype: :py:class:`numpy.ndarray`

		.. NOTE::

			Be sure to return the data when you're done.
		"""
		return ImageOps.decode(percept_data)
