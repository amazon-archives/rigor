from vision.database import transactional, reader, RowMapper, uuid_transform

def resolution_transform(value, column_name, row):
	if value is None:
		return None
	return (row['x_resolution'], row['y_resolution'])

imageMapper = RowMapper(field_mappings={'x_resolution': 'resolution', 'y_resolution': None}, field_transforms={'locator':uuid_transform, 'resolution':resolution_transform})

class DatabaseMapper(object):
	""" Reads and write Images to database """

	def __init__(self, database):
		self._db = database

	def _get_next_id(self, cursor, name):
		sql = "SELECT NEXTVAL('{0}_id_seq');".format(name)
		cursor.execute(sql)
		row = cursor.fetch_one()
		return row.values()[0]

	@reader
	def get_image_by_id(self, image_id):
		""" Retrieves the image from the database """
		pass

	def _get_image_by_id(self, cursor, image_id):
		sql = "SELECT id, locator, hash, stamp, sensor, x_resolution, y_resolution, format, depth, location, source FROM image WHERE id = %s;"
		cursor.execute(sql, (image_id, ))
		image = cursor.fetch_only_one(imageMapper)
		image['tags'] = self._get_tags_by_image_id(cursor, image_id)
		image['annotations'] = self._get_annotations_by_image_id(cursor, image_id)
		return image

	@reader
	def get_images_for_analysis(self, domain, limit=None):
		"""
		Retrieves all images for the domain from the database, used for
		algorithm analysis.  The optional limit limits the number of
		images returned
		"""
		pass

	def _get_images_for_analysis(self, cursor, domain, limit):
		sql = "SELECT distinct(image.id), image.locator, image.format FROM annotation LEFT JOIN image ON annotation.image_id = image.id WHERE annotation.domain = %s"
		if limit:
			sql = "SELECT * FROM (" + sql + ") sub ORDER BY random() LIMIT %s;"
			cursor.execute(sql, (domain, limit))
		else:
			sql += " ORDER BY image.id;"
			cursor.execute(sql, (domain, ))
		rows = cursor.fetch_all()
		images = list()
		for row in rows:
			image = imageMapper.map_row(row)
			sql = "SELECT model FROM annotation WHERE image_id = %s";
			cursor.execute(sql, (row[0], ))
			image['annotations'] = [dict(model=row[0]) for row in cursor.fetch_all()]
			images.append(image)
		return images

	def _get_tags_by_image_id(self, cursor, image_id):
		sql = "SELECT name FROM tag where image_id = %s;"
		cursor.execute(sql, (image_id, ))
		rows = cursor.fetch_all()
		return [row[0] for row in rows]

	@transactional
	def create_image(self, image):
		""" Stores the image metadata in the database, setting its id """
		pass

	def _create_image(self, cursor, image):
		id = self._get_next_id(cursor, 'image')
		sql = "INSERT INTO image (id, locator, hash, stamp, sensor, x_resolution, y_resolution, format, depth, location, source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		cursor.execute(sql, (id, image['locator'], image['hash'], image['stamp'], image['sensor'], image['resolution'][0], image['resolution'][1], image['format'], image['depth'], image['location'], image['source']))
		image['id'] = id
		if image['tags']:
			self._create_tags(cursor, image['tags'], id)
		if image['annotations']:
			for annotation in image['annotations']:
				self._create_annotation(cursor, annotation, id)

	def _create_tags(self, cursor, tags, image_id):
		sql = "INSERT INTO tag (image_id, name) VALUES (%s, %s);"
		cursor.executemany(sql, [(image_id, tag) for tag in tags])

	@reader
	def get_annotation_by_id(self, annotation_id):
		""" Retrieves the annotation from the database """
		pass

	def _get_annotation_by_id(self, cursor, annotation_id):
		sql = "SELECT id, stamp, boundary, domain, rank, model FROM annotation WHERE id = %s;"
		cursor.execute(sql, (annotation_id, ))
		return cursor.fetch_only_one()

	def _get_annotations_by_image_id(self, cursor, image_id):
		sql = "SELECT id, stamp, boundary, domain, rank, model FROM annotation WHERE image_id = %s;"
		cursor.execute(sql, (image_id, ))
		return cursor.fetch_all()

	@transactional
	def create_annotation(self, annotation, image_id):
		""" Stores the annotation in the database, setting its id """
		pass

	def _create_annotation(self, cursor, annotation, image_id):
		id = self._get_next_id(cursor, 'annotation')
		sql = "INSERT INTO annotation (id, image_id, stamp, boundary, domain, rank, model) VALUES (%s, %s, %s, %s, %s, %s, %s);"
		cursor.execute(sql, (id, image_id, annotation['stamp'], annotation['boundary'], annotation['domain'], annotation['rank'], annotation['model']))
		annotation['id'] = id
