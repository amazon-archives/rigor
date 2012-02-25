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

class Runner(object):
	""" Class for running algorithms against test images """

	def __init__(self, runnable, domain, parameters, limit=None, random=False, imageid=None, tags_require=None, tags_exclude=None):
		"""
		The domain dictates which algorithm to run (algorithm is fixed per domain),
		and which images to use as sources.  The limit is an optional maximum number
		of images to use as sources
		"""
		#if domain not in rigor.domain.kModules:
			#raise ValueError("Unknown domain '{0}'".format(domain))
		#domain_module = __import__('rigor.domain.{0}'.format(domain), fromlist=['init', 'run'])
		runnable.init(parameters)
		self._domain = domain
		self._parameters = parameters
		self._limit = limit
		self._random = random
		self._imageid = imageid
		if imageid and (limit or random):
			raise ValueError("use either imageid or random/limit options, not both")
		self._logger = rigor.logger.getLogger('.'.join((__name__, self.__class__.__name__)))
		self._database = rigor.database.Database()
		self._database_mapper = DatabaseMapper(self._database)
		self._domain_module = runnable
		if kMaxWorkers != 1:
			self._pool = Pool(int(config.get('global', 'max_workers')))
		self._tags_require = tags_require
		self._tags_exclude = tags_exclude

	def set_parameters(self, parameters):
		self._parameters = parameters
		self._domain_module.set_parameters(parameters)

	def run(self):
		self._logger.debug('Fetching image IDs from database')
		if self._imageid:
			images = self._database_mapper.get_image_for_analysis(self._domain, self._imageid)
		else:
			images = self._database_mapper.get_images_for_analysis(self._domain, self._limit, self._random, self._tags_require, self._tags_exclude)
		image_config = partial(self._domain_module.run, parameters=self._parameters)
		self._logger.debug('Processing {0} images'.format(len(images)))
		if kMaxWorkers != 1:
			return self._pool.map(image_config, images)
		else:
			return map(image_config, images)
