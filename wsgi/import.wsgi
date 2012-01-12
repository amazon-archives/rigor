""" Adds an image to the rigor database """

from rigor.importer import Importer

from webob import Request, Response

import json
import tempfile
import shutil
import os.path

from datetime import datetime

kImporter = Importer(tempfile.gettempdir())

def application(environ, start_response):
	req = Request(environ)
	res = Response(content_type='application/json', headerlist=[('Allow', 'POST')])

	if req.method != 'POST':
		res.body = json.dumps({'status': 'error', 'message': 'Only POST requests allowed'})
		res.status_int = 405
	else:
		missing = list()
		for key in ('image', 'source', 'tags'):
			if key not in req.params:
				missing.append(key)
		if missing:
			res.body = json.dumps({'status': 'error', 'message': 'Required fields missing', 'hint': missing})
			res.status_int = 400
		else:
			with tempfile.NamedTemporaryFile(prefix='rigor-tmp-', delete=True) as image:
				shutil.copyfileobj(req.params['image'].file, image)
				image.seek(0)

				metadata = dict()
				if 'sensor' in req.params:
					metadata['sensor'] = req.params['sensor']
				if 'location' in req.params:
					metadata['location'] = req.params['location']
				metadata['source'] = req.params['source']
				metadata['tags'] = req.params.getall('tags')
				image_path = os.path.abspath(os.path.join(tempfile.gettempdir(), image.name))
				metadata = kImporter.import_image(image_path, image.name, metadata)

			if metadata is None:
				# image already exists
				res.body = json.dumps({'status': 'error', 'message': 'Image already exists; not imported'})
				res.status_int = 409
			else:
				datetime_handler = lambda obj: obj.isoformat() if isinstance(obj, datetime) else None
				res.body = json.dumps({'status': 'ok', 'message': 'Image successfully uploaded', 'hint': metadata}, default=datetime_handler)
				res.status_int = 200

	return res(environ, start_response)
