import rigor.applicator
import rigor.imageops

import argparse
import json
import time

### algorithm ###
def _algorithm_prefetch_default(image):
	pass

def _algorithm_postfetch_default(image, image_data):
	return image_data

def _algorithm_run_default(image_data):
	raise NotImplementedError()

def _algorithm_parse_annotations_default(annotations):
	return annotations[0]['model']

def create_algorithm(domain, prefetch_hook=_algorithm_prefetch_default, postfetch_hook=_algorithm_postfetch_default, run_hook=_algorithm_run_default, parse_annotations_hook=_algorithm_parse_annotations_default, **kwargs):
	def _create_algorithm(image):
		prefetch_hook(image)
		with rigor.imageops.fetch(image) as image_file:
			image_data = postfetch_hook(image, rigor.imageops.read(image_file))
			t0 = time.time()
			result = run_hook(image_data)
			elapsed = time.time() - t0
			annotations = parse_annotations_hook(image['annotations'])
			if 'annotations' in image:
				del(image['annotations'])
			if 'tags' in image:
				del(image['tags'])
			return (image, result, annotations, elapsed)
	return _create_algorithm

### runner ###
def _arguments_default(parser):
	pass

def parse_arguments(arguments_hook=_arguments_default, **kwargs):
	parser = argparse.ArgumentParser(description='Runs algorithm on relevant images')
	parser.add_argument('-p', '--parameters', required=False, help='Path to parameters file, or JSON block containing parameters')
	limit = parser.add_mutually_exclusive_group()
	limit.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
	limit.add_argument('-i', '--image_id', type=int, metavar='IMAGE ID', required=False, help='Single image ID to run')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	parser.add_argument('--tag_require', action='append', dest='tags_require', required=False, help='Tag that must be present on selected images')
	parser.add_argument('--tag_exclude', action='append', dest='tags_exclude', required=False, help='Tag that must not be present on selected images')
	arguments_hook(parser)
	return parser.parse_args()

def _set_parameters_default(parameters):
	pass

def _load_parameters_default(args):
	"""
	If parameters are specified, it tries to read them as a JSON block.  If it
	can't, it tries to open them and read them as a JSON file.  If it can't do
	that either, then it just passes them along unchanged.
	"""
	if not args.parameters:
		return None
	try:
		parameters = json.loads(args.parameters)
	except ValueError:
		try:
			with open(args.parameters, 'rb') as param_file:
				parameters = json.load(param_file)
		except ValueError:
			parameters = args.parameters
	return parameters

def _evaluate_hook_default(results):
	for result in results:
		print '\t'.join(str(field) for field in result)

def create_applicator(domain, load_parameters_hook=_load_parameters_default, set_parameters_hook=_set_parameters_default, evaluate_hook=_evaluate_hook_default, **hooks):
	args = parse_arguments(**hooks)
	parameters = load_parameters_hook(args)
	set_parameters_hook(parameters)
	algorithm = create_algorithm(domain, **hooks)
	if args.image_id:
		applicator = rigor.applicator.SingleApplicator(domain, algorithm, parameters, evaluate_hook, image_id)
	else:
		applicator = rigor.applicator.Applicator(domain, algorithm, parameters, evaluate_hook, limit=args.limit, random=args.random, tags_require=args.tags_require, tags_exclude=args.tags_exclude)
	return applicator
