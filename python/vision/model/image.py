class Image(object):
	""" Holds image metadata """
	modes = {'1': 1, 'L': 8, 'RGB': 24, 'RGBA': 32}

	def __init__(self):
		self.id = None
		self.locator = None
		self.hash = None
		self.stamp = None
		self.sensor = None
		self.resolution = None
		self.format = None
		self.depth = None
		self.location = None
		self.source = None
		self.tags = list()
		self.annotations = list()

	def __str__(self):
		return "Image {0}".format(vars(self))
