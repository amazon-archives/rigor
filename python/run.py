import vision.core
import vision.runner

import sys
import argparse

def main():
	parser = argparse.ArgumentParser(description='Runs algorithm on relevant images')
	parser.add_argument('domain', help='Domain to run')
	parser.add_argument('parameters', help='Path to parameters file')
	args = parser.parse_args()
	i = vision.runner.Runner(args.domain)
	i.set_parameters(args.parameters)
	i.run()

if __name__ == '__main__':
	main()
