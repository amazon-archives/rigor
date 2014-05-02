""" Helpers needed by multiple adapters """

class DictRow(object):
	""" Implementation for a row behaving as a dict """

	def __init__(self, row, column_names):
		self._row = row
		self._column_names = column_names
		self._column_map = dict(zip(column_names, row))

	def __getitem__(self, key):
		try:
			return self._row[key]
		except TypeError:
			return self._column_map[key]

	def __contains__(self, key):
		return key in self._column_map

	def __iter__(self):
		for column in self._row:
			yield column

	def values(self):
		return self._row

	def __getattr__(self, name):
		return getattr(self._row, name)

	def iteritems(self):
		return ((column, self._column_map[column]) for column in self._column_names)

class DictCursor(object):
	""" A cursor-like object that can fetch columns by name as well as by numeric index """
	def __init__(self, cursor):
		self._cursor = cursor

	def fetchone(self):
		columns = [column[0] for column in self._cursor.description]
		row = self._cursor.fetchone()
		return DictRow(row, columns)

	def fetchmany(self, size=None):
		if size == None:
			size = self.arraysize
		columns = [column[0] for column in self._cursor.description]
		rows = self._cursor.fetchmany(size)
		return [DictRow(row, columns) for row in rows]

	def fetchall(self):
		columns = [column[0] for column in self._cursor.description]
		rows = self._cursor.fetchall()
		return [DictRow(row, columns) for row in rows]

	def __getattr__(self, name):
		return getattr(self._cursor, name)

