from vision.model.image import Image
from vision.model.annotation import Annotation
from vision.database import transactional, reader, RowMapper

import Image as PILImage

imageMapper = RowMapper(Image)
annotationMapper = RowMapper(Annotation)

class ObjectMapper(object):
	""" Reads and write Images to database """

	def __init__(self, database):
		self._db = database

	def _get_next_id(self, cursor, name):
		sql = "SELECT NEXTVAL('{0}_id_seq');".format(name)
		cursor.execute(sql)
		row = cursor.fetchone()
		return row.values()[0]

	@reader
	def get_image_by_id(self, image_id):
		""" Retrieves the image from the database """
		pass

	def _get_image_by_id(self, cursor, image_id):
		sql = "SELECT id, locator, hash, stamp, sensor, x_resolution, y_resolution, format, depth, location, source FROM image WHERE id = %s;"
		cursor.execute(sql, (image_id, ))
		image = cursor.fetch_only_one_object(imageMapper)
		image.tags = _get_tags_by_image_id(image_id)
		image.annotations = _get_annotations_by_image_id(image_id)
		return image

	def _get_tags_by_image_id(self, cursor, image_id):
		sql = "SELECT name FROM tag where image_id = %s;"
		cursor.execute(sql, (image_id, ))
		rows = cursors.fetchall()
		return [row[0] for row in rows]

	@transactional
	def create_image(self, image):
		""" Stores the image metadata in the database, setting its id """
		pass

	def _create_image(self, cursor, image):
		id = self._get_next_id(cursor, 'image')
		sql = "INSERT INTO image (id, locator, hash, stamp, sensor, x_resolution, y_resolution, format, depth, location, source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		cursor.execute(sql, (id, image.locator, image.hash, image.stamp, image.sensor, image.resolution[0], image.resolution[1], image.format, image.depth, image.location, image.source))
		image.id = id
		if image.tags:
			self._create_tags(cursor, image.tags, id)
		if image.annotations:
			for annotation in image.annotations:
				self._create_annotation(cursor, annotation, id)

	def _create_tags(self, cursor, tags, image_id):
		sql = "INSERT INTO tag (image_id, name) VALUES (%s, %s);"
		cursor.executemany(sql, [(image_id, tag) for tag in tags])

	@reader
	def get_annotation_by_id(self, annotation_id):
		""" Retrieves the annotation from the database """
		pass

	def _get_annotation_by_id(self, cursor, annotation_id):
		sql = "SELECT id, stamp, boundary, grouping, rank, model, value FROM annotation WHERE id = %s;"
		cursor.execute(sql, (annotation_id, ))
		annotation = cursor.fetch_only_one_object(annotationMapper)
		return annotation

	def _get_annotations_by_image_id(self, cursor, image_id):
		sql = "SELECT id, stamp, boundary, grouping, rank, model, value FROM annotation WHERE image_id = %s;"
		cursor.execute(sql, (image_id, ))
		annotations = cursor.fetch_all_objects(annotationMapper)
		return annotations

	@transactional
	def create_annotation(self, annotation, image_id):
		""" Stores the annotation in the database, setting its id """
		pass

	def _create_annotation(self, cursor, annotation, image_id):
		id = self._get_next_id(cursor, 'annotation')
		sql = "INSERT INTO annotation (id, image_id, stamp, boundary, grouping, rank, model, value) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
		cursor.execute(sql, (id, image_id, annotation.stamp, annotation.boundary, annotation.grouping, annotation.rank, annotation.model, annotation.value))
		annotation.id = id
