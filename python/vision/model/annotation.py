class Annotation(object):
	""" Holds an image annotation """

	def __init__(self):
		self.id = None
		self.stamp = None
		self.boundary = None
		self.domain = None
		self.rank = None
		self.model = None

	def __str__(self):
		return "Annotation {0}".format(vars(self))
