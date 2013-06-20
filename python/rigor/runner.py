"""
Runs an algorithm across a set of images.  Result is a report containing image
ID, detected model, expected model, and elapsed time
"""
from rigor.config import config

import rigor.logger
import rigor.database
import rigor.dbmapper

import abc
import json
import argparse

kMaxWorkers = int(config.get('global', 'max_workers'))
if kMaxWorkers > 1:
	from multiprocessing.pool import Pool

class BaseRunner(object):
	"""
	The base class for Runner objects, which fetch a set of images and apply
	the Algorithm instance to each
	"""
	__metaclass__ = abc.ABCMeta

	def __init__(self, algorithm, arguments=None):
		self._logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self._algorithm = algorithm
		self._parameters = None
		self._arguments = None
		self.parse_arguments(arguments)
		self._algorithm.set_arguments(self._arguments)
		self.load_parameters()
		self.set_parameters()

	def parse_arguments(self, arguments):
		"""
		Parses command-line arguments

		Sets self._arguments with the parsed argument object
		"""
		parser = argparse.ArgumentParser(description='Runs algorithm on relevant images', conflict_handler='resolve')
		parser.add_argument('-p', '--parameters', required=False, help='Path to parameters file, or JSON block containing parameters')
		self.add_arguments(parser)
		if arguments:
			self._arguments = parser.parse_args(arguments)
		else:
			self._arguments = parser.parse_args()

	def add_arguments(self, parser):
		"""
		This method can be overridden to add additional arguments or otherwise
		modify the argument parser before it runs parse_args()
		"""
		pass

	def load_parameters(self):
		"""
		Given some item stored in the parameters attribute of the parsed arguments,
		this method will first interpret the data as json, falling back to
		interpreting it as a path to a file containing json.  If both of those
		approaches fail, the contents of the parameter itself will be used.  In any
		of these cases, the result is saved as self._parameters.
		"""
		if not self._arguments.parameters:
			return None
		try:
			self._parameters = json.loads(self._arguments.parameters)
		except ValueError:
			try:
				with open(self._arguments.parameters, 'rb') as param_file:
					self._parameters = json.load(param_file)
			except ValueError:
				self._parameters = self._arguments.parameters

	def set_parameters(self):
		"""
		This can be used to set the parameters, stored in self._parameters, on the
		Algorithm object, once load_parameters() has run.
		"""
		pass

	@abc.abstractmethod
	def run(self):
		"""
		This is the method called to run the algorithm.  It must be overridden.
		"""
		pass

	def evaluate(self, results): # pylint: disable=R0201
		"""
		This takes the final output of all applications of the algorithm and
		formats it into a useful report.  It can optionally return results (that's
		up to the implementer), but its main function should be to create reports
		and format output.  The default implementation simply prints the results to
		stdout
		"""
		print(results)
		return results # why not?

class DatabaseRunner(BaseRunner):
	"""
	Runner base class that uses the database to discover images for evaluation
	"""
	__metaclass__ = abc.ABCMeta

	def __init__(self, algorithm, arguments=None):
		BaseRunner.__init__(self, algorithm, arguments)
		self._database = rigor.database.Database(self._arguments.database)
		self._database_mapper = rigor.dbmapper.DatabaseMapper(self._database)

	def parse_arguments(self, arguments):
		"""
		Parses command-line arguments

		Sets self._arguments with the parsed argument object
		"""
		parser = argparse.ArgumentParser(description='Runs algorithm on relevant images', conflict_handler='resolve')
		parser.add_argument('-p', '--parameters', required=False, help='Path to parameters file, or JSON block containing parameters')
		limit = parser.add_mutually_exclusive_group()
		limit.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
		limit.add_argument('-i', '--image_id', type=int, metavar='IMAGE ID', required=False, help='Single image ID to run')
		parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
		parser.add_argument('--tag_require', action='append', dest='tags_require', required=False, help='Tag that must be present on selected images')
		parser.add_argument('--tag_exclude', action='append', dest='tags_exclude', required=False, help='Tag that must not be present on selected images')
		parser.add_argument('database', help='Name of the database to use')
		self.add_arguments(parser)
		if arguments:
			self._arguments = parser.parse_args(arguments)
		else:
			self._arguments = parser.parse_args()

class Runner(DatabaseRunner):
	""" Class for running algorithms against test images """

	def __init__(self, algorithm, domain, arguments=None):
		"""
		The domain dictates which images to use as sources. The limit is an
		optional maximum number of images to use as sources.  If random, images
		will be pulled in random order, up to limit; otherwise, images will be
		pulled in sequential order.  Tags are used to control the image selection
		further.
		"""
		DatabaseRunner.__init__(self, algorithm, arguments)
		self._domain = domain
		if kMaxWorkers > 1:
			self._pool = Pool(int(config.get('global', 'max_workers')))

	def run(self):
		""" Runs the algorithm on the images matching the supplied arguments """
		self._logger.debug('Fetching image IDs from database')
		images = self._database_mapper.get_images_for_analysis(self._domain, self._arguments.limit, self._arguments.random, self._arguments.tags_require, self._arguments.tags_exclude)
		self._logger.debug('Processing {0} images'.format(len(images)))
		if kMaxWorkers > 1:
			return self.evaluate(self._pool.map(self._algorithm.apply, images))
		else:
			return self.evaluate(map(self._algorithm.apply, images))

class SingleRunner(DatabaseRunner):
	""" Class for running algorithms against a single test image """

	def __init__(self, algorithm, domain, image_id, arguments=None):
		"""
		algorithm is the algorithm to apply.  domain chooses where to search for
		annotations.  image_id is the single image ID to test.  arguments is what
		the argument parser will use; if None, sys.args will be used.
		"""
		DatabaseRunner.__init__(self, algorithm, arguments)
		self._domain = domain
		self._image_id = image_id

	def run(self):
		""" Runs the algorithm on the image and returns the result """
		image = self._database_mapper.get_image_for_analysis(self._domain, self._image_id)
		self._logger.debug('Processing image ID {}'.format(self._image_id))
		return self.evaluate([self._algorithm.apply(image)])
