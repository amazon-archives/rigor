import vision.importer

import argparse

def main():
	parser = argparse.ArgumentParser(description='Imports images and metadata into the database')
	parser.add_argument('directories', metavar='dir', nargs='+', help='Directory containing images and metadata to import')
	parser.add_argument('-m', '--move', action="store_true", dest='move', default=False, help='Move files into repository instead of copying')
	args = parser.parse_args()
	for directory in args.directories:
		i = vision.importer.Importer(directory, args.move)
		i.run()

if __name__ == '__main__':
	main()
