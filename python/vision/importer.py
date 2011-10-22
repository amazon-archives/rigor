import os
import vision.logger
import vision.database

class Importer(object):
	""" Class containing methods for importing images into the Vision framework """

	def __init__(self, path):
		self._path = path
		self._logger = vision.logger.getLogger(".".join((__name__, self.__class__.__name__)))

	def run(self):
		""" Imports all images from the path, returning the number processed """
		count = 0
		for entry in os.listdir(self._path):
			absfile = os.path.abspath(os.path.join(self._path, entry))
			if not os.path.isfile(absfile):
				continue
			(basename, sep, extension) = entry.rpartition('.')
			if not sep:
				self._logger.warn("Could not find separator for {0}".format(entry))
				continue
