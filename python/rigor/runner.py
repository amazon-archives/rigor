"""
Runs an algorithm across a set of images.  Result is a report containing image
ID, detected model, expected model, and elapsed time
"""
from rigor.config import config
from rigor.dbmapper import DatabaseMapper

import rigor.domain
import rigor.logger
import rigor.database

from functools import partial

kMaxWorkers = int(config.get('global', 'max_workers'))
if kMaxWorkers != 1:
	from multiprocessing.pool import Pool

class BaseRunner(object):
	def __init__(self, domain, parameters, runnable=None):
		if not runnable:
			if domain not in rigor.domain.kModules:
				raise ValueError("Unknown domain '{0}'".format(domain))
			runnable = __import__('rigor.domain.{0}'.format(domain), fromlist=['init', 'run'])
		self._runnable = runnable
		self._domain = domain
		self._parameters = parameters
		self._logger = rigor.logger.getLogger('.'.join((__name__, self.__class__.__name__)))
		self._database = rigor.database.Database()
		self._database_mapper = DatabaseMapper(self._database)
		runnable.init(parameters)

	def set_parameters(self, parameters):
		self._parameters = parameters
		self._runnable.set_parameters(parameters)

class Runner(BaseRunner):
	""" Class for running algorithms against test images """

	def __init__(self, domain, parameters, runnable=None, limit=None, random=False, tags_require=None, tags_exclude=None):
		"""
		The domain dictates which images to use as sources.  If a runnable is
		supplied, it will control the algorithm to be run.  Otherwise, the domain
		will be used to find an algorithm runner.  The limit is an optional maximum
		number of images to use as sources.  If random, images will be pulled in
		random order, up to limit; otherwise, images will be pulled in sequential
		order.  Tags are used to control the image selection further.
		"""
		BaseRunner.__init__(self, domain, parameters, runnable)
		self._limit = limit
		self._random = random
		if kMaxWorkers != 1:
			self._pool = Pool(int(config.get('global', 'max_workers')))
		self._tags_require = tags_require
		self._tags_exclude = tags_exclude

	def run(self):
		self._logger.debug('Fetching image IDs from database')
		images = self._database_mapper.get_images_for_analysis(self._domain, self._limit, self._random, self._tags_require, self._tags_exclude)
		image_config = partial(self._runnable.run, parameters=self._parameters)
		self._logger.debug('Processing {0} images'.format(len(images)))
		if kMaxWorkers != 1:
			return self._pool.map(image_config, images)
		else:
			return map(image_config, images)

class SingleRunner(BaseRunner):
	""" Class for running algorithms against single test images """

	def __init__(self, domain, parameters, image_id, runnable=None):
		"""
		If a runnable is supplied, it will control the algorithm to be run.
		Otherwise, the domain will be used to find an algorithm runner.
		"""
		BaseRunner.__init__(self, domain, parameters, runnable)
		self._image_id = image_id

	def run(self):
		image = self._database_mapper.get_image_for_analysis(self._domain, self._image_id)
		self._logger.debug('Processing image ID {}'.format(self._image_id))
		return self._runnable.run(image, parameters=self._parameters)
