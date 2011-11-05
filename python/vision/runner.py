"""
Runs an algorithm across a set of images.  Result is a report containing image
ID, detected model, expected model, and elapsed time
"""
from vision.config import config
from vision.dbmapper import DatabaseMapper

import vision.domain
import vision.logger
import vision.database

from multiprocessing.pool import ThreadPool

# TODO: until we make Domains non-objects somehow, allowing a process pool,
# we're better off not using multiprocessing.

class Runner(object):
	""" Class for running algorithms against test images """

	def __init__(self, domain, limit=None):
		"""
		The domain dictates which algorithm to run (algorithm is fixed per domain),
		and which images to use as sources.  The limit is an optional maximum number
		of images to use as sources
		"""
		if domain not in vision.domain.kModules:
			raise ValueError("Unknown domain '{0}'".format(domain))
		module = __import__('vision.domain.{0}'.format(domain), fromlist=list('Domain'))
		Domain = getattr(module, 'Domain')
		self._domain = domain
		self._limit = limit
		self._logger = vision.logger.getLogger('.'.join((__name__, self.__class__.__name__)))
		self._database = vision.database.Database()
		self._database_mapper = DatabaseMapper(self._database)
		self._domain_object = Domain()
		self._pool = ThreadPool(int(config.get('global', 'max_worker_threads')))

	def set_parameters(self, parameters):
		self._domain_object.set_parameters(parameters)

	def run(self):
		self._logger.debug('Fetching image IDs from database')
		images = self._database_mapper.get_images_for_analysis(self._domain, self._limit)
		self._logger.debug('Processing {0} images'.format(len(images)))
		return self._pool.map(self._domain_object.run, images)
