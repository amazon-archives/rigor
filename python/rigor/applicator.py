"""
Applies an algorithm to a set of images.  Result is a report containing image
ID, detected model, expected model, and elapsed time
"""
from rigor.config import config
from rigor.dbmapper import DatabaseMapper

import rigor.logger
import rigor.database

import itertools

kMaxWorkers = int(config.get('global', 'max_workers'))
if kMaxWorkers != 1:
	from multiprocessing.pool import Pool

class BaseApplicator(object):
	def __init__(self, domain, algorithm, parameters, evaluate_hook):
		self._domain = domain
		self._algorithm = algorithm
		self._parameters = parameters
		self._evaluate_hook = evaluate_hook
		self._logger = rigor.logger.getLogger('.'.join((__name__, self.__class__.__name__)))
		self._database = rigor.database.Database()
		self._database_mapper = DatabaseMapper(self._database)

class Applicator(BaseApplicator):
	""" Class for running algorithms against test images """

	def __init__(self, domain, algorithm, parameters, evaluate_hook, limit=None, random=False, tags_require=None, tags_exclude=None):
		"""
		The domain dictates which images to use as sources.  The algorithm is what
		gets run against each image.  The limit is an optional maximum number of
		images to use as sources.  If random, images will be pulled in random
		order, up to limit; otherwise, images will be pulled in sequential order.
		Tags are used to control the image selection further.
		"""
		BaseApplicator.__init__(self, domain, algorithm, parameters, evaluate_hook)
		self._limit = limit
		self._random = random
		if kMaxWorkers != 1:
			self._pool = Pool(int(config.get('global', 'max_workers')))
		self._tags_require = tags_require
		self._tags_exclude = tags_exclude

	def apply(self):
		self._logger.debug('Fetching image IDs from database')
		images = self._database_mapper.get_images_for_analysis(self._domain, self._limit, self._random, self._tags_require, self._tags_exclude)
		self._logger.debug('Processing {0} images'.format(len(images)))
		if kMaxWorkers != 1:
			return self._evaluate_hook(self._pool.map(self._algorithm, images))
		else:
			return self._evaluate_hook(map(self._algorithm, images))

class SingleApplicator(BaseApplicator):
	""" Class for running algorithms against single test images """

	def __init__(self, domain, algorithm, parameters, evaluate_hook, image_id):
		"""
		If a applicable is supplied, it will control the algorithm to be run.
		Otherwise, the domain will be used to find an algorithm runner.
		"""
		BaseApplicator.__init__(self, domain, algorithm, parameters, evaluate_hook)
		self._image_id = image_id

	def apply(self):
		image = self._database_mapper.get_image_for_analysis(self._domain, self._image_id)
		self._logger.debug('Processing image ID {}'.format(self._image_id))
		return self._evaluate_hook(map(self._algorithm,image))
