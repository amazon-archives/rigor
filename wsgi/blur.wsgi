import rigor.database
import rigor.imageops

from rigor.dbmapper import DatabaseMapper, image_mapper

from webob import Request, Response

import sys
import os.path
import urlparse
import urllib

from datetime import datetime

kImageBaseUrl = '/rigor/images'
kImageMaxWidth = 640
kImageMaxHeight = 640

gDatabase = rigor.database.Database()
gDbMapper = DatabaseMapper(gDatabase)

def get_image(last_image):
	sql = "SELECT * FROM image WHERE "
	args = list()
	if last_image:
		sql += "id < %s AND "
		args.append(last_image)
	sql += "id NOT IN (SELECT DISTINCT(image_id) FROM annotation WHERE annotation.domain = 'blur' OR annotation.domain = 'money') ORDER BY stamp DESC LIMIT 1;"
	cursor = gDatabase.get_cursor()
	try:
		cursor.execute(sql, args)
		image = cursor.fetch_one(image_mapper)
	finally:
		gDatabase.rollback(cursor)
	return image

def delete_annotation(image_id):
	sql = "DELETE FROM annotation WHERE domain = 'blur' AND image_id = %s;"
	cursor = gDatabase.get_cursor()
	try:
		cursor.execute(sql, (image_id, ))
		gDatabase.commit(cursor)
	except:
		gDatabase.rollback(cursor)
		raise

def application(environ, start_response):
	message = '&nbsp;'
	image_id = None
	undoable = False

	req = Request(environ)
	res = Response(content_type='text/html')

	if req.method == 'POST':
		undo = req.params.get('u', None)
		blur = req.params.get('b', False)
		noblur = req.params.get('n', False)
		image_id = req.params.get('i', None)

		if undo and image_id:
			delete_annotation(image_id)
			message = 'Annotation for {} removed'.format(image_id)
		elif blur or noblur:
			model = ("no" if noblur else "") + "blur"
			annotation = {
					'stamp': datetime.utcnow(),
					'boundary': None,
					'domain': 'blur',
					'rank': None,
					'model': model,
			}
			gDbMapper.create_annotation(annotation, image_id)
			message = 'Image {} marked {}'.format(image_id, model)
			undoable = True
		else:
			message = 'Image {} skipped'.format(image_id)

	image = get_image(image_id)
	image_path = "/".join((kImageBaseUrl, image['locator'][0:2], image['locator'][2:4], ".".join((image['locator'], image['format']))))

	res.status_int = 200
	res.body = """<html>
	<head>
		<title>Blur Classification</title>
	</head>
	<body>
		<div>
			<p>{}</p>
			<p>The image below is: </p>
			<form method="POST">
				<input type="hidden" name="i" value="{}" />
				<input type="submit" name="b" value="Blurry" />
				<input type="submit" name="n" value="Not Blurry" />
				<input type="submit" name="s" value="Skip" />
				{}<input type="submit" name="u" value="Undo Last" />{}
			</form>
		</div>
		<div>
			<img src="{}" style="max-width: {}px; max-height: {}px;" />
		</div>
	</body>
</html>""".format(message, image['id'], "" if undoable else "<!-- ", "" if undoable else " -->", image_path, kImageMaxWidth, kImageMaxHeight)

	return res(environ, start_response)
