""" The text detector domain """

import rigor.imageops
import itertools
import subprocess
from sibyl.text import TextDetector
import time
from cStringIO import StringIO

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
	if parameters.has_key("evaluate_windows") and parameters["evaluate_windows"]:
		with rigor.imageops.fetch(image) as image_file:
			image_data = rigor.imageops.read(image_file)
			#print(image_data.mode)
			t0 = time.time()
			detected, undetected = _detector.evaluate_windows(image_data)
			elapsed = time.time() - t0
			#print("Boom!")
			tmp = StringIO()
			#tmp.write("mergeboxesv2([")
			tmp.write("disp([")
			first = True
			for grouping_info in detected:
				if not first:
					tmp.write(";")
				first = False
				roi =",".join(str(x) for x in itertools.chain.from_iterable(grouping_info['roi']))
				tmp.write(",".join((str(grouping_info['layer']), roi, str(grouping_info['weight']))))
			tmp.write("])")
			subprocess.call(["octave","--path","/home/mudigonda/Projects/rigor/python/","--eval",tmp.getvalue()])
			print("Octave done!")
			return (image['id'],)
	else:
		with rigor.imageops.fetch(image) as image_file:
			image_data = rigor.imageops.read(image_file)
			t0 = time.time()
			detected = _detector.detect(image_data)
			elapsed = time.time() - t0
			return (image['id'], detected, [annotation["boundary"] for annotation in image['annotations']], elapsed)
