import rigor.database
import rigor.imageops

from rigor.dbmapper import DatabaseMapper, image_mapper

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

def get_random_image():
	sql = "SELECT * FROM image WHERE id NOT IN (SELECT DISTINCT(image_id) FROM annotation WHERE annotation.domain = 'blur' OR annotation.domain = 'money') ORDER BY random() LIMIT 1;"
	cursor = gDatabase.get_cursor()
	try:
		cursor.execute(sql)
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
	status = '200 OK'
	message = ''
	image_id = ''
	if environ['REQUEST_METHOD'] == 'POST':
		try:
			request_body_size = int(environ.get('CONTENT_LENGTH', 0))
		except ValueError:
			request_body_size = 0

		query = urlparse.parse_qs(environ['wsgi.input'].read(request_body_size))
		undo = query.get('u', [None,])[0]
		last_image = query.get('l', [None,])[0]
		if undo and last_image:
			delete_annotation(last_image)
			message = 'Annotation for {} removed'.format(last_image)
		blur = query.get('b', [False, ])[0]
		# noblur is a check to ensure something was actually selected here
		noblur = query.get('n', [False, ])[0]
		image_id = query.get('i', [None,])[0]
		if blur or noblur:
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
		else:
			message = 'Image {} skipped'.format(image_id)

	image = get_random_image()
	image_path = "/".join((kImageBaseUrl, image['locator'][0:2], image['locator'][2:4], ".".join((image['locator'], image['format']))))

	output = """<html>
	<head>
		<title>Blur Classification</title>
	</head>
	<body>
		<div>
			<p>{}</p>
			<p>The image below is: </p>
			<form method="POST">
				<input type="hidden" name="i" value="{}" />
				<input type="hidden" name="l" value="{}" />
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
</html>""".format(message, image['id'], image_id, "" if image_id else "<!-- ", "" if image_id else " -->", image_path, kImageMaxWidth, kImageMaxHeight)

	response_headers = [('Content-type', 'text/html'),
			('Content-Length', str(len(output)))]

	start_response(status, response_headers)

	return [output]
