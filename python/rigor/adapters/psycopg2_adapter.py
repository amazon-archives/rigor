""" psycopg2 adapter support for Rigor """

from rigor.config import config
import rigor.database

import sys
import psycopg2
import psycopg2.extensions
import psycopg2.extras

from psycopg2.extensions import register_type
from psycopg2.extras import register_uuid
from psycopg2.pool import ThreadedConnectionPool

from contextlib import contextmanager

import ConfigParser

def template(function):
	"""
	Executes the SQL in the function while connected to the template database
	"""
	def _execute(*args, **kwargs):
		dsn = Database.build_dsn(rigor.database.kTemplateDatabase)
		connection = psycopg2.connect(dsn)
		try:
			connection.autocommit = True
			cursor = connection.cursor()
			cursor.execute(function(*args, **kwargs))
		finally:
			connection.close()
	return _execute

class RigorCursor(psycopg2.extras.DictCursor, rigor.database.RigorCursorMixin):
	pass

class Database(rigor.database.Database):
	""" Container for a database connection pool """

	def __init__(self, database):
		super(Database, self).__init__(database)
		register_type(psycopg2.extensions.UNICODE)
		register_uuid()
		dsn = Database.build_dsn(database)
		self._pool = ThreadedConnectionPool(config.get('database', 'min_database_connections'), config.get('database', 'max_database_connections'), dsn)

	@staticmethod
	def build_dsn(database):
		""" Builds the database connection string from config values """
		dsn = "dbname='{0}' host='{1}' port={2}".format(database, config.get('database', 'host'), config.getint('database', 'port'))
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
		connection = self._pool.getconn()
		cursor = connection.cursor(cursor_factory=RigorCursor)
		try:
			yield cursor
		except psycopg2.IntegrityError as error:
			exc_info = sys.exc_info()
			self.rollback(cursor)
			raise rigor.database.IntegrityError, exc_info[1], exc_info[2]
		except psycopg2.DatabaseError as error:
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
		""" Closes a cursor and releases the connection to the pool """
		cursor.close()
		self._pool.putconn(cursor.connection)

	def commit(self, cursor):
		""" Commits the transaction, then closes the cursor """
		cursor.connection.commit()
		self._close_cursor(cursor)

	def rollback(self, cursor):
		""" Rolls back the transaction, then closes the cursor """
		cursor.connection.rollback()
		self._close_cursor(cursor)

	def __del__(self):
		self._pool.closeall()
