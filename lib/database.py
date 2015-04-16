""" Database abstraction for Rigor """

import sqlalchemy as sa
from sqlalchemy.orm.session import sessionmaker
from contextlib import contextmanager

#: Mapping of database object types to names
kNamingConvention = {
	'ix': '%(table_name)s_%(column_0_name)s_idx',
	'uq': '%(table_name)s_%(column_0_name)s_key',
	'ck': '%(table_name)s_%(constraint_name)s_check',
	'fk': '%(table_name)s_%(referred_table_name)s_%(referred_column_0_name)s_fkey',
	'pk': '%(table_name)s_pkey',
}

kDSNKeys = ('driver', 'username', 'password', 'host', 'port')

class ContextSession(object):
	"""
	Wraps a SQLAlchemy session in a context manager

	:param session: SQLAlchemy session
	:param bool commit: If :py:const:`True`, the session will be committed when it exits the context. If :py:const:`False`, or if there is an exception, the session will be rolled back.
	"""
	def __init__(self, session, commit=True):
		self.session = session
		self._commit = commit

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		try:
			if exc_type is None:
				if self._commit:
					self.session.commit()
			else:
				self.session.rollback()
		finally:
			self.session.close()

	def __getattr__(self, name):
		return getattr(self.session, name)

class BaseDatabase(object):
	"""
	Abstracts a database engine and sessions

	:param str database: The name of the database
	:param config: Configuration data
	:type config: :py:class:`~rigor.config.RigorConfiguration`
	"""

	@classmethod
	def build_url(cls, database, config):
		"""
		Given the configuration and a database name, this method will generate a SQLAlchemy URL

		:param str database: Name of the database to connect to
		:param config: The Rigor configuration
		:return: a URL
		"""
		args = [config.get('database', key) if ('database', key) in config else None for key in kDSNKeys]
		args.append(database)
		url = sa.engine.url.URL(*args)
		return url

	def __init__(self, database, config):
		self.name = database
		self._config = config
		url = Database.build_url(database, config)
		self._engine = sa.create_engine(url)
		self._metadata = sa.MetaData(bind=self._engine, naming_convention=kNamingConvention)
		self._sessionmaker = sessionmaker(bind=self._engine)

	def get_session(self, commit=True):
		"""
		Gets a new session from the pool. The session in wrapped in a :py:func:`~contextlib.contextmanager`.

		:param bool commit: If :py:const:`True`, the session will be committed when it exits the context. If :py:const:`False`, or if there is an exception, the session will be rolled back.
		:return: new session
		"""
		return ContextSession(self._sessionmaker(), commit)

Database = BaseDatabase
