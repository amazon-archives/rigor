"""
Runs an algorithm across a set of images.  Result is a report containing image
ID, detected model, expected model, and elapsed time
"""
from vision.config import config
from vision.objectmapper import ObjectMapper

import vision.domain
import vision.logger
import vision.database


import multiprocessing

class Runner(object):
	""" Class for running algorithms against test images """

	def __init__(self, domain):
		"""
		The domain dictates which algorithm to run (algorithm is fixed per domain),
		and which images to use as sources.
		"""
		if domain not in vision.domain.kModules:
			raise ValueError("Unknown domain '{0}'".format(domain))
		self._domain = domain
		self._logger = vision.logger.getLogger('.'.join((__name__, self.__class__.__name__)))
		self._database = vision.database.Database()
		self._object_mapper = ObjectMapper(self._database)
		__import__('vision.domain.{0}'.format(domain), fromlist=list('Domain'))
		self._domain_object = Domain()
		self._pool = multiprocessing.Pool(min(multiprocessing.cpu_count(), config.get('global', 'max_worker_threads')))

	def set_parameters(self, parameters):
		self._domain_object.set_parameters(parameters)

	def run(self):
		images = self._object_mapper.get_images_by_domain(self._domain)
		return self._pool.map(self._domain_object.run, images)
