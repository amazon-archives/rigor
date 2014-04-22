""" Database abstraction for Rigor """

from rigor.config import config

from contextlib import contextmanager

import ConfigParser
import exceptions
from abc import ABCMeta, abstractmethod

kTemplateDatabase = 'template1'

class Error(exceptions.StandardError):
	"""
	See PEP-249
	Exception that is the base class of all other error exceptions.
	You can use this to catch all errors with one single except statement.
	"""
	pass

class DatabaseError(Error):
	"""
	See PEP-249
	Exception raised for errors that are related to the database.
	"""
	pass

class IntegrityError(DatabaseError):
	"""
	See PEP-249
	Exception raised when the relational integrity of the database is affected,
	e.g. a foreign key check fails.
	"""
	pass

class RigorCursorMixin(object):
	""" Mixed in with a DictCursor to add row mapping and enhanced fetch capabilities """

	def fetch_all(self, row_mapper=None):
		""" Fetches all rows, applying row mapper if any """
		if row_mapper:
			return (row_mapper.map_row(row) for row in self.fetchall())
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
		Fetches one and only one row.  Raises IntegrityError if there is not
		exactly one row found.
		"""
		if self.rowcount != 1:
			raise IntegrityError("Expected one record found, actually found %d. Query: %s" % (self.rowcount, self.query))
		return self.fetch_one(row_mapper)

class Database(object):
	""" Abstracts a database and its connections """
	__metaclass__ = ABCMeta

	@abstractmethod
	def __init__(self, database):
		self._database_name = database

	@abstractmethod
	def get_cursor(self, commit=True):
		""" Gets a cursor from a connection in the pool """
		raise NotImplementedError("Must be implemented in the adaptor")

	@abstractmethod
	def commit(self, cursor):
		""" Commits the transaction, then closes the cursor """
		raise NotImplementedError("Must be implemented in the adaptor")

	@abstractmethod
	def rollback(self, cursor):
		""" Rolls back the transaction, then closes the cursor """
		raise NotImplementedError("Must be implemented in the adaptor")

	@staticmethod
	def instance(database):
		adaptor_name = config.get('database', 'adaptor')
		adaptor = __import__("rigor.adaptors.{}_adaptor".format(adaptor_name), fromlist=["rigor.adaptors", ])
		return adaptor.Database(database)

	@staticmethod
	def cls():
		adaptor_name = config.get('database', 'adaptor')
		adaptor = __import__("rigor.adaptors.{}_adaptor".format(adaptor_name), fromlist=["rigor.adaptors", ])
		return adaptor.Database

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

def transactional(function):
	"""
	Runs a function wrapped in a single transaction.
	"""
	def _execute(self, *args, **kwargs):
		real_function_name = "_" + function.__name__
		real_function = getattr(self, real_function_name)
		with self._db.get_cursor() as cursor: # pylint: disable=W0212
			return real_function(cursor, *args, **kwargs)
	return _execute

def uuid_transform(value, column_name, row):
	""" Returns a UUID object """
	if value is None:
		return None
	return row[column_name].hex

def polygon_transform(value, column_name, row):
	""" Returns a polygon as a list of tuples (points) """
	if value is None:
		return None
	return list(eval(row[column_name]))

def polygon_tuple_adapter(polygon):
	""" Returns a string formatted in a way that PostgreSQL recognizes as a polygon, given a sequence of pairs """
	if polygon is None:
		return None
	return str(tuple(tuple([int(coord) for coord in point]) for point in polygon))
