""" Exceptions for the Vision application """

class VisionError(Exception):
	""" Base class for exceptions in Vision """
	pass

class ThreadingError(VisionError):
	""" Errors in threading """
	pass

class DatabaseError(VisionError):
	""" Errors in database """

	def __init__(self, parent):
		self._parent = parent

	def __str__(self):
		return str(self._parent)

	def __unicode__(self):
		return unicode(self._parent)

class DuplicateError(DatabaseError):
	""" Duplicate data where it is forbidden """
	pass
