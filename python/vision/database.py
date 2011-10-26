""" Database connection stuff """

import vision.constants

from vision.exceptions import DatabaseError, DuplicateError

import psycopg2
import psycopg2.extensions
import psycopg2.extras

from psycopg2.extensions import register_type
from psycopg2.extensions import register_adapter
from psycopg2.extensions import adapt
from psycopg2.pool import ThreadedConnectionPool
from psycopg2 import ProgrammingError
from psycopg2 import IntegrityError

class VisionCursor(psycopg2.extras.DictCursor):
	""" Helper methods for DBAPI cursors """

	def fetch_only_one(self):
		"""
		Like fetchone, but raises an exception if there are any number of
		rows except one
		"""
		if self.rowcount != 1:
			raise DatabaseError("Expected one record found, actually found %d. Query: %s" % (self.rowcount, self.query))
		return self.fetchone()


	def fetch_all_objects(self, row_mapper):
		"""
		Fetches all rows as objects, constructed using the specified
		row mapper
		"""
		rows = self.fetchall()
		return [row_mapper.map_row(row) for row in rows]

	def fetch_one_object(self, row_mapper):
		"""
		Fetches zero or one object, constructed using the specified
		row mapper
		"""
		row = self.fetchone()
		if row is None:
			return None
		return row_mapper.map_row(row)

	def fetch_only_one_object(self, row_mapper):
		"""
		Fetches one and only one object, constructed using the specified
		row mapper
		"""
		if self.rowcount != 1:
			raise DatabaseError("Expected one record found, actually found %d" % self.rowcount)
		row = self.fetchone()
		return row_mapper.map_row(row)

	def fetch_some(self, limit, offset=0):
		"""
		Fetches up to limit number of rows, with a possible offset
		"""
		if self.rowcount == 0:
			return list()
		elif offset > self.rowcount:
			log.warn('Offset of %s > %s' % (offset, self.rowcount))
			return list()
		self.scroll(offset, mode='absolute')
		return self.fetchmany(limit)

	def fetch_some_objects(self, row_mapper, limit, offset=0):
		"""
		Fetches up to limit number of objects, with a possible offset
		"""
		if self.rowcount == 0:
			return list()
		elif offset > self.rowcount:
			return list()
		self.scroll(offset, mode='absolute')
		rows = self.fetchmany(limit)
		return [row_mapper.map_row(row) for row in rows]

class Database(object):
	""" Holds a pool of connections to a database """

	def __init__(self, database, host, username=None, password=None, ssl=False):
		register_type(psycopg2.extensions.UNICODE)
		self._databaseName = database
		dsn = "dbname='%s' host='%s'" % (database, host)
		if ssl:
			dsn += " sslmode='require'"
		if username:
			dsn += " user='%s' password='%s'" % (username, password)
		self._pool = ThreadedConnectionPool(vision.constants.kMinimumDatabaseConnections, vision.constants.kMaximumDatabaseConnections, dsn)

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
	""" Maps a database row (as a dict) to a returned class """
	def __init__(self, object_type, field_mappings=None, field_transforms=None):
		if field_mappings is None:
			field_mappings = dict()
		if field_transforms is None:
			field_transforms = dict()
		self._object_type = object_type
		self._field_mappings = field_mappings
		self._field_transforms = field_transforms

	def map_row(self, row):
		""" The actual method that does the mapping """
		# First we'll build a list of None arguments to fill in the blanks
		arg_count = self._object_type.__init__.im_func.func_code.co_argcount
		arg_count -= 1 # ignore self argument
		arguments = [None for argument in range(0, arg_count)]
		# Now we'll instantiate the object with all of our Nones
		obj = self._object_type(*arguments)
		self.apply_values(obj, row)
		return obj

	def apply_values(self, obj, row):
		"""
		Applies all entries in the supplied dictionary as object
		attributes, mapping names if necessary
		"""
		if not isinstance(row, dict):
			row = dict(row)
		for column_name, value in row.iteritems():
			if self._field_mappings.has_key(column_name):
				attribute_name = self._field_mappings[column_name]
			if self._field_transforms.has_key(attribute_name):
				value = self._field_transforms[attribute_name](value, column_name, row)
			setattr(obj, attribute_name, value)

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
	except IntegrityError as err:
		self._db.rollback(cursor)
		raise DuplicateError(err)
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
