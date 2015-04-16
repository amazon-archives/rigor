""" General utilities to make things easier in Rigor """

import json
import os
import errno
from datetime import datetime

kISO8601Format = '%Y-%m-%dT%H:%M:%SZ'
kISO8601FormatMicroseconds = '%Y-%m-%dT%H:%M:%S.%fZ'

def parse_timestamp(timestamp):
	"""
	Given input, returns a :py:class:`datetime.datetime`.  Input can either be a :py:class:`datetime.datetime`, or a string ISO 8601 format

	:param timestamp: timestamp to parse
	:return: parsed timestamp
	:rtype: :py:class:`~datetime.datetime`
	"""
	if isinstance(timestamp, datetime):
		return timestamp
	try:
		return datetime.strptime(timestamp, kISO8601FormatMicroseconds)
	except ValueError:
		return datetime.strptime(timestamp, kISO8601Format)

class RigorJSONEncoder(json.JSONEncoder):
	""" A JSON encoder that knows how to handle types used in Rigor """
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.isoformat() + 'Z'
		return json.JSONEncoder.default(self, obj)

def ensure_path_exists(path, mode=0o777):
	"""
	Same as :py:func:`os.makedirs`, but it does not raise an exception if the leaf directory already exists.
	"""
	try:
		os.makedirs(path, mode)
	except OSError as err:
		if err.errno != errno.EEXIST:
			raise err
