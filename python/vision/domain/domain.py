""" Base class for domains """

class Domain(object):
	def __init__(self, parameters=None):
		"""
		Initializes the object.  Parameters are either a dict of parameters to pass
		in, or a path to a file containing configuration.
		"""
		raise NotImplementedError

	def set_parameters(self, parameters):
		"""
		Changes the stored parameters used for running algorithms.  Parameters are
		either a dict of parameters to pass in, or a path to a file containing
		configuration.
		"""
		self._parameters = parameters

	def run(self, image):
		"""
		Runs the algorithm on the Image model object, returning a tuple of
		(detected_models, time_elapsed)
		"""
		raise NotImplementedError
