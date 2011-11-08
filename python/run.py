import vision.runner

import argparse

def main():
	parser = argparse.ArgumentParser(description='Runs algorithm on relevant images')
	parser.add_argument('domain', help='Domain to run')
	parser.add_argument('parameters', help='Path to parameters file')
	parser.add_argument('-l', '--limit', metavar='COUNT', required=False, help='Maximum number of images to use')
	args = parser.parse_args()
	i = vision.runner.Runner(args.domain, args.parameters, args.limit)
	for result in i.run():
		print("\t".join([str(x) for x in result]))

if __name__ == '__main__':
	main()
