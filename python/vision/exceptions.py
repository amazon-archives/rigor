""" Exceptions for the Vision application """

class VisionError(Exception):
	""" Base class for exceptions in Vision """
	pass

class DatabaseError(VisionError):
	""" Errors in database access """
