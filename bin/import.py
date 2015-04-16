#!/usr/bin/env python

import rigor.interop
from rigor.config import RigorDefaultConfiguration

import argparse
import os
import glob
import json

def main():
	parser = argparse.ArgumentParser(description='Imports percepts and metadata into the database')
	parser.add_argument('-n', '--no-copy', action='store_true', default=False, help="Don't copy data into the Rigor repository; just keep it in place (not recommended")
	parser.add_argument('database', help='Database to use')
	parser.add_argument('metadata', help='Path to metadata file to import or directory with multiple metadata files where each metadata file contains a single percept')
	args = parser.parse_args()

	metadata = args.metadata
	if os.path.isdir(metadata):
		metadata_paths = glob.glob(os.path.join(metadata, '*.json'))
		metadata = list()
		for metadata_path in metadata_paths:
			with open(metadata_path, "rb") as metadata_file:
				metadata.append(json.load(metadata_file))

	config = RigorDefaultConfiguration()
	copy_data = not args.no_copy
	i = rigor.interop.Importer(config, args.database, metadata, copy_data)
	i.run()

if __name__ == '__main__':
	main()
