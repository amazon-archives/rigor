""" The money detector domain """

import vision.imageops

from sibyl.money import MoneyDetector

import time

class Domain(object):
	def __init__(self):
		"""
		Initializes the object.  Parameters are either a dict of parameters to pass
		to the algorithm, or a path to a file containing them.
		"""
		self._detector = MoneyDetector()

	def set_parameters(self, parameters):
		"""
		Changes the stored parameters used for running algorithms.  Parameters are
		either a dict of parameters to pass in to the algorithm, or a path to a
		file containing them.
		"""
		# Underlying C implementation requires a dict instance, in particular
		if isinstance(parameters, dict):
			self._detector.set_configuration(parameters)
		else:
			self._detector.load_configuration(parameters)

	def run(self, image):
		"""
		Runs the algorithm on the Image model object object, returning a tuple of
		(detected model, time elapsed)
		"""
		with vision.imageops.fetch(image) as image_file:
			image_data = vision.imageops.read(image_file)
			t0 = time.time()
			detected = self._detector.read_model(image_data)
			elapsed = time.time() - t0
			return (image['id'], detected, image['annotations'][0]['model'], elapsed) # XXX only supports one annotation
