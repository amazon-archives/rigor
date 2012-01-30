#!/usr/bin/env python

"""
Removes all expired annotation locks from the database

Example crontab entry:

PYTHONPATH=/data/rigor/python
*/5 * * * * /usr/local/bin/python /data/rigor/tools/expire-locks.py
"""

import rigor.database

from rigor.dbmapper import DatabaseMapper

class LockExpirer(object):
	""" Expires locks in the database """
	def __init__(self):
		self._dbmapper = DatabaseMapper(rigor.database.Database())

	def run(self):
		self._dbmapper.expire_locks()

if __name__ == '__main__':
	expirer = LockExpirer()
	expirer.run()
