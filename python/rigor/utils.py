""" General utilities to make things easier in Rigor """

import json
from datetime import datetime

class RigorJSONEncoder(json.JSONEncoder):
	""" A JSON encoder that knows how to handle types used in Rigor """
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.isoformat()
		return json.JSONEncoder.default(self, obj)
