""" pg8000 adaptors for Rigor """

from rigor.config import config
from contextlib import contextmanager
from rigor.adaptors.common import DictCursor

import pg8000
import sys
import warnings
import rigor.database
import ConfigParser

def template(function):
	"""
	Executes the SQL in the function while connected to the template database
	"""
	def _execute(*args, **kwargs):
		connection = pg8000.connect(**Database.build_dsn(rigor.database.kTemplateDatabase))
		connection.autocommit = True
		try:
			cursor = connection.cursor()
			cursor.execute(function(*args, **kwargs))
		finally:
			connection.close()
	return _execute

class RigorCursor(rigor.database.RigorCursorMixin, DictCursor):
	def execute(self, operation, args=None, stream=None):
		"""
		Splits statements separated by a semicolon into multiple calls to
		execute. This is mainly for compatibility with psycopg2, and is used
		here for executing patch files.
		"""
		operations = (op.strip() for op in operation.split(';') if len(op.strip()) > 0)
		for op in operations:
			self._cursor.execute(op, args, stream)

class Database(rigor.database.Database):
	""" Abstracts a database and its connections """

	def __init__(self, database):
		super(Database, self).__init__(database)
		self._dsn = Database.build_dsn(database)

	@staticmethod
	def build_dsn(database):
		""" Builds the database connection parameters from config values """
		dsn = { 'database': database, 'host': config.get('database', 'host') }
		try:
			ssl = config.getboolean('database', 'ssl')
			if ssl:
				dsn['ssl'] = ssl
		except ConfigParser.Error:
			pass
		try:
			username = config.get('database', 'username')
			dsn['user'] = username
		except ConfigParser.Error:
			pass
		try:
			password = config.get('database', 'password')
			dsn['password'] = password
		except ConfigParser.Error:
			pass
		return dsn

	@staticmethod
	@template
	def create(name):
		""" Creates a new database with the given name """
		return "CREATE DATABASE {0};".format(name)

	@staticmethod
	@template
	def drop(name):
		""" Drops the database with the given name """
		return "DROP DATABASE {0};".format(name)

	@staticmethod
	@template
	def clone(source, destination):
		"""
		Copies the source database to a new destination database.  This may fail if
		the source database is in active use.
		"""
		return "CREATE DATABASE {0} WITH TEMPLATE {1};".format(destination, source)

	@contextmanager
	def get_cursor(self, commit=True):
		""" Gets a cursor from a connection in the pool """
		connection = pg8000.connect(**self._dsn)
		cursor = RigorCursor(connection.cursor())
		try:
			yield cursor
		except pg8000.IntegrityError as error:
			exc_info = sys.exc_info()
			self.rollback(cursor)
			raise rigor.database.IntegrityError, exc_info[1], exc_info[2]
		except pg8000.DatabaseError as error:
			exc_info = sys.exc_info()
			self.rollback(cursor)
			raise rigor.database.DatabaseError, exc_info[1], exc_info[2]
		except:
			exc_info = sys.exc_info()
			self.rollback(cursor)
			raise exc_info[0], exc_info[1], exc_info[2]
		else:
			if commit:
				self.commit(cursor)
			else:
				self.rollback(cursor)

	def _close_cursor(self, cursor):
		""" Closes a cursor and its connection """
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			connection = cursor.connection
		cursor.close()
		connection.close()

	def commit(self, cursor):
		""" Commits the transaction, then closes the cursor """
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			connection = cursor.connection
		connection.commit()
		self._close_cursor(cursor)

	def rollback(self, cursor):
		""" Rolls back the transaction, then closes the cursor """
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			connection = cursor.connection
		connection.rollback()
		self._close_cursor(cursor)
