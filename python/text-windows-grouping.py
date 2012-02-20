import rigor.runner
import itertools
import argparse
import json
import subprocess

def main():
	parser = argparse.ArgumentParser(description='Runs algorithm on relevant images')
	parser.add_argument('domain', help='Domain to run')
	parser.add_argument('parameters', help='Path to parameters file, or JSON block containing parameters')
	parser.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	args = parser.parse_args()
	try:
		parameters = json.loads(args.parameters)
	except ValueError:
		try:
			with open(args.parameters, 'rb') as param_file:
				parameters = json.load(param_file)
		except ValueError:
			parameters = args.parameters
	i = rigor.runner.Runner(args.domain, parameters, args.limit, args.random)
	tmp = list()
	for result in i.run():
#		print("\t".join([str(x) for x in result]))
#		for box in result[1]:
		#	for x,y in box:
#			print box 
		for grouping_info in result[1]:
			roi =",".join(str(x) for x in itertools.chain.from_iterable(grouping_info['roi']))
			tmp.append(",".join((str(grouping_info['layer']), roi, str(grouping_info['weight']))))
		tmp = "[{}]".format(";".join(tmp))
		subprocess.call(["octave","--eval","pedro({})".format(tmp)]) 
if __name__ == '__main__':
	main()
