import rigor.runner

import argparse

def main():
	parser = argparse.ArgumentParser(description='Runs algorithm on relevant images')
	parser.add_argument('domain', help='Domain to run')
	parser.add_argument('parameters', help='Path to parameters file')
	parser.add_argument('-l', '--limit', metavar='COUNT', required=False, help='Maximum number of images to use')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	args = parser.parse_args()
	i = rigor.runner.Runner(args.domain, args.parameters, args.limit, args.random)
	for result in i.run():
		print("\t".join([str(x) for x in result]))

if __name__ == '__main__':
	main()
