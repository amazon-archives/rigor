""" The money detector domain """

import rigor.imageops

from sibyl.money import MoneyDetector
import time

_detector = None

def set_parameters(parameters):
	"""
	Changes the stored parameters used for running algorithms.  Parameters are
	either a dict of parameters to pass in to the algorithm, or a path to a
	file containing them.
	"""
	global _detector
	# Underlying C implementation requires a dict instance, in particular
	if isinstance(parameters, dict):
		_detector.set_configuration(parameters)
	else:
		_detector.load_configuration(parameters)

def init(parameters):
	""" Initializes the MoneyDetector and sets its parameters """
	global _detector
	_detector = MoneyDetector()
	set_parameters(parameters)

def run(image):
	"""
	Runs the algorithm on the Image model object object, returning a tuple of
	(detected model, time elapsed)
	"""
	global _detector
	with rigor.imageops.fetch(image) as image_file:
		image_data = rigor.imageops.read(image_file)
		t0 = time.time()
		detected = _detector.read_model(image_data)
		elapsed = time.time() - t0
		return (image['id'], detected, image['annotations'][0]['model'], elapsed) # XXX only supports one annotation
