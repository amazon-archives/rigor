""" The money detector domain """

import vision.imageops

from sibyl.money import MoneyDetector

class Domain(BaseDomain):
	def __init__(self):
		"""
		Initializes the object.  Parameters are either a dict of parameters to pass
		to the algorithm, or a path to a file containing them.
		"""
		super(Domain, self).__init__(self)
		self._detector = sibyl.money.MoneyDetector()

	def set_parameters(self, parameters):
		"""
		Changes the stored parameters used for running algorithms.  Parameters are
		either a dict of parameters to pass in to the algorithm, or a path to a
		file containing them.
		"""
		if hasattr(parameters, '__getitem__'):
			self._detector.setConfiguration(parameters)
		else:
			self._detector.loadConfiguration(parameters)

	def run(self, image):
		"""
		Runs the algorithm on the Image model object object, returning a tuple of
		(detected model, time elapsed)
		"""
		with imageops.fetch(image) as image_file:
			image_data = imageops.read(image_file)
			t0 = time.time()
			detected = self._detector.readModel(image_data)
			elapsed = time.time() - t0
			return (image.id, detected, image.annotations[0].model, elapsed) # XXX only supports one annotation
