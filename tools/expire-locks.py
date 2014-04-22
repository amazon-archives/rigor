#!/usr/bin/env python

"""
Removes all expired annotation locks from the database

Example crontab entry:

PYTHONPATH=/data/rigor/python
* * * * * /usr/local/bin/python /data/rigor/tools/expire-locks.py rigor
"""

import rigor.database
import argparse

from rigor.dbmapper import DatabaseMapper
from rigor.database import Database

class LockExpirer(object):
	""" Expires locks in the database """
	def __init__(self, database):
		self._dbmapper = DatabaseMapper(Database.instance(database))

	def run(self):
		self._dbmapper.expire_locks()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Removes expired annotation locks")
	parser.add_argument("database", help="Database to use")
	args = parser.parse_args()
	expirer = LockExpirer(args.database)
	expirer.run()
