""" The money detector domain """

import vision.imageops
from vision.domain.domain import Domain

from sibyl.money import MoneyDetector

class MoneyDomain(Domain):
	def __init__(self, parameters):
		self._detector = sibyl.money.MoneyDetector()
		self.set_parameters(parameters)

	def set_parameters(self, parameters):
		super(MoneyDomain, self).set_parameters(parameters)
		if hasattr(parameters, '__getitem__'):
			self._detector.setConfiguration(parameters)
		else:
			self._detector.loadConfiguration(parameters)

	def run(self, image):
		with imageops.fetch(image) as image_file:
			image_data = imageops.read(image_file)
			t0 = time.time()
			detected = self._detector.readModel(image_data)
			elapsed = time.time() - t0
			return ([detected, ], elapsed)
