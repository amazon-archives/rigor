""" Database connection stuff """

from vision.config import config

import psycopg2
import psycopg2.extensions
import psycopg2.extras

from psycopg2.extensions import register_type
from psycopg2.extensions import register_adapter
from psycopg2.extensions import adapt
from psycopg2.pool import ThreadedConnectionPool
from psycopg2 import ProgrammingError
from psycopg2 import IntegrityError

import ConfigParser
import uuid

class VisionCursor(psycopg2.extras.DictCursor):
	""" Helper methods for DBAPI cursors """

	def fetch_all(self, row_mapper=None):
		""" Fetches all rows, applying row mapper if any """
		if row_mapper:
			return [row_mapper.map_row(row) for row in self.fetchall()]
		else:
			return self.fetchall()

	def fetch_one(self, row_mapper=None):
		""" Fetches zero or one row, applying row mapper if any """
		row = self.fetchone()
		if row is None:
			return None
		if row_mapper is None:
			return row
		return row_mapper.map_row(row)

	def fetch_only_one(self, row_mapper=None):
		"""
		Like fetchone, but raises an exception if there are any number of
		rows except one
		"""
		if self.rowcount != 1:
			raise IntegrityError("Expected one record found, actually found %d. Query: %s" % (self.rowcount, self.query))
		return self.fetch_one(row_mapper)

	def fetch_some(self, limit, offset=0, row_mapper=None):
		""" Fetches up to limit number of objects, with a possible offset """
		if self.rowcount == 0:
			return list()
		elif offset > self.rowcount:
			return list()
		self.scroll(offset, mode='absolute')
		if row_mapper:
			return [row_mapper.map_row(row) for row in self.fetchmany(limit)]
		else:
			return self.fetchmany(limit)

class Database(object):
	""" Holds a pool of connections to a database """

	def __init__(self):
		register_type(psycopg2.extensions.UNICODE)
		self._database_name = config.get('database', 'database')
		dsn = "dbname='{0}' host='{1}'".format(self._database_name, config.get('database', 'host'))
		try:
			ssl = config.getboolean('database', 'ssl')
			if ssl:
				dsn += " sslmode='require'"
		except ConfigParser.Error:
			pass
		try:
			username = config.get('database', 'username')
			dsn += " user='{0}'".format(username)
		except ConfigParser.Error:
			pass
		try:
			password = config.get('database', 'password')
			dsn += " password='{0}'".format(password)
		except ConfigParser.Error:
			pass
		self._pool = ThreadedConnectionPool(config.get('database', 'min_database_connections'), config.get('database', 'max_database_connections'), dsn)

	def get_cursor(self):
		""" Gets a cursor in its own connection on the database """
		connection = self._get_connection()
		cursor = connection.cursor(cursor_factory=VisionCursor)
		return cursor

	def commit(self, cursor):
		""" Commits any update queries on the cursor, then closes it """
		cursor.connection.commit()
		self._close_cursor(cursor)

	def rollback(self, cursor):
		""" Rolls back any update queries on the cursor, then closes it """
		cursor.connection.rollback()
		self._close_cursor(cursor)

	def _get_connection(self):
		""" Returns a connection from the database, abstracted so we can debug """
		return self._pool.getconn()

	def _close_cursor(self, cursor):
		""" Closes a cursor and returns its connection to the pool """
		cursor.close()
		try:
			self._pool.putconn(cursor.connection)
		except Exception, e:
			log.warn("Failed to close cursor: %s" % e)

	def __del__(self):
		self._pool.closeall()

class RowMapper(object):
	"""
	Maps a database row (as a dict) to a returned dict, with transformed fields
	as necessary
	"""
	def __init__(self, field_mappings=None, field_transforms=None):
		if field_mappings is None:
			field_mappings = dict()
		if field_transforms is None:
			field_transforms = dict()
		self._field_mappings = field_mappings
		self._field_transforms = field_transforms

	def map_row(self, row):
		"""
		Transforms keys and values as necessary to transform a database row into a
		returned dict
		"""
		new = dict()
		for column_name, value in row.iteritems():
			if self._field_mappings.has_key(column_name):
				key = self._field_mappings[column_name]
			else:
				key = column_name
			if key is None:
				continue
			if self._field_transforms.has_key(key):
				value = self._field_transforms[key](value, column_name, row)
			new[key] = value
		return new

def _run_database_method(self, _commit_transaction, function, *args, **kwargs):
	real_function_name = "_" + function.__name__
	real_function = getattr(self, real_function_name)

	cursor = self._db.get_cursor()
	try:
		retval = real_function(cursor, *args, **kwargs)
		if _commit_transaction:
			self._db.commit(cursor)
		else:
			self._db.rollback(cursor)
	except:
		self._db.rollback(cursor)
		raise
	return retval

def transactional(function):
	""" Runs a function wrapped in a single transaction """
	def _execute(self, *args, **kwargs):
		return _run_database_method(self, True, function, *args, **kwargs)
	return _execute

def reader(function):
	""" Runs a function wrapped in a single transaction, rolled back at the end """
	def _execute(self, *args, **kwargs):
		return _run_database_method(self, False, function, *args, **kwargs)
	return _execute

def uuid_transform(value, column_name, row):
	""" Returns a UUID object """
	if value is None:
		return None
	return uuid.UUID(row[column_name]).hex
