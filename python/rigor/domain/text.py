""" The text detector domain """

import rigor.imageops

from sibyl.text import TextDetector
import time

_detector = None
_paramaters = None

def set_parameters(parameters):
	"""
	Changes the stored parameters used for running algorithms.  Parameters are
	either a dict of parameters to pass in to the algorithm, or a path to a
	file containing them.
	"""
	global _parameters
	global _detector
	_parameters = parameters
	_detector.set_configuration(parameters)

def init(parameters):
	""" Initializes the TextDetector and sets its parameters """
	global _parameters
	global _detector
	_parameters = parameters
	_detector = TextDetector()
	set_parameters(parameters)

def run(image, parameters=None):
	"""
	Runs the algorithm on the Image model object object, returning a tuple of
	(detected model, time elapsed)
	"""
	global _parameters
	global _detector
	if parameters is not None and parameters != _parameters:
		set_parameters(parameters)
	with rigor.imageops.fetch(image) as image_file:
		image_data = rigor.imageops.read(image_file)
		t0 = time.time()
		detected = _detector.detect(image_data)
		elapsed = time.time() - t0
		return (image['id'], detected, ",".join(annotation["model"] for annotation in image['annotations']), elapsed)
