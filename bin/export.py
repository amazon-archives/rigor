#!/usr/bin/env python

import rigor.interop
from rigor.config import RigorDefaultConfiguration

import argparse

def main():
	parser = argparse.ArgumentParser(description='Exports all data from the database')
	parser.add_argument('database', help='Database to use')
	parser.add_argument('filename', help='Metadata filename to create')
	args = parser.parse_args()
	config = RigorDefaultConfiguration()
	i = rigor.interop.Exporter(config, args.database, args.filename)
	i.run()

if __name__ == '__main__':
	main()
