#!/usr/bin/env python

from rigor.interop import Exporter
from rigor.config import RigorDefaultConfiguration

import argparse

def main():
	parser = argparse.ArgumentParser(description='Exports all data from the database')
	parser.add_argument('database', help='Database to use')
	parser.add_argument('filename', help='Metadata filename to create')
	parser.add_argument('--config', '-c', help='override default rigor.ini to use')
	args = parser.parse_args()
	if args.config:
		config = RigorDefaultConfiguration(args.config)
	else:
		config = RigorDefaultConfiguration()
	exporter = Exporter(config, args.database, args.filename)
	exporter.run()

if __name__ == '__main__':
	main()
