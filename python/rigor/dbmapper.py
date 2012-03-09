from rigor.database import transactional, RowMapper, uuid_transform, polygon_transform, polygon_tuple_adapter

import uuid
from datetime import datetime, timedelta
import psycopg2

def resolution_transform(value, column_name, row):
	if value is None:
		return None
	return (row['x_resolution'], row['y_resolution'])

image_mapper = RowMapper(field_mappings={'x_resolution': 'resolution', 'y_resolution': None}, field_transforms={'locator':uuid_transform, 'resolution':resolution_transform})
annotation_mapper = RowMapper(field_transforms={'boundary':polygon_transform})

class DatabaseMapper(object):
	""" Reads and write Images to database """

	def __init__(self, database):
		self._db = database

	def _get_next_id(self, cursor, name):
		sql = "SELECT NEXTVAL('{0}_id_seq');".format(name)
		cursor.execute(sql)
		row = cursor.fetch_one()
		return row.values()[0]

	@transactional
	def get_only_image_by_id(self, image_id):
		"""
		Retrieves the image, but none of its tags or annotations, from the database
		"""
		pass

	def _get_only_image_by_id(self, cursor, image_id):
		sql = "SELECT id, locator, hash, stamp, sensor, x_resolution, y_resolution, format, depth, location, source FROM image WHERE id = %s;"
		cursor.execute(sql, (image_id, ))
		image = cursor.fetch_only_one(image_mapper)
		return image

	@transactional
	def get_image_by_id(self, image_id):
		""" Retrieves the image from the database """
		pass

	def _get_image_by_id(self, cursor, image_id):
		image = self._get_only_image_by_id(cursor, image_id)
		image['tags'] = self._get_tags_by_image_id(cursor, image_id)
		image['annotations'] = self._get_annotations_by_image_id(cursor, image_id)
		return image

	@transactional
	def get_images_for_analysis(self, domain, limit=None, random=False):
		"""
		Retrieves all images for the domain from the database, used for
		algorithm analysis.  The optional limit limits the number of
		images returned.  If random, the images will be randomly selected.
		Otherwise, images will be returned sorted by ID.
		"""
		pass

	def _get_images_for_analysis(self, cursor, domain, limit, random):
		sql = "SELECT * FROM (SELECT distinct(image.id), image.locator, image.format FROM annotation LEFT JOIN image ON annotation.image_id = image.id WHERE annotation.domain = %s) image ORDER BY "
		if random and limit:
			sql += "random()"
		else:
			sql += "image.id"

		if limit:
			sql += " LIMIT %s;"
			cursor.execute(sql, (domain, limit))
		else:
			sql += ";"
			cursor.execute(sql, (domain, ))
		rows = cursor.fetch_all()
		images = list()
		for row in rows:
			image = image_mapper.map_row(row)
			sql = "SELECT model, boundary FROM annotation WHERE image_id = %s AND domain = %s;";
			cursor.execute(sql, (row[0], domain, ))
			image['annotations'] = cursor.fetch_all(annotation_mapper)
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

	@transactional
	def get_annotation_by_id(self, annotation_id):
		""" Retrieves the annotation from the database """
		pass

	def _get_annotation_by_id(self, cursor, annotation_id):
		sql = "SELECT id, stamp, boundary, domain, rank, model FROM annotation WHERE id = %s;"
		cursor.execute(sql, (annotation_id, ))
		return cursor.fetch_only_one(annotation_mapper)

	def _get_annotations_by_image_id(self, cursor, image_id):
		sql = "SELECT id, stamp, boundary, domain, rank, model FROM annotation WHERE image_id = %s;"
		cursor.execute(sql, (image_id, ))
		return cursor.fetch_all(annotation_mapper)

	@transactional
	def update_annotation_model(self, annotation_id, model):
		"""
		Replaces model in the database with new model.  The timestamp will be
		updated to the current time.
		"""
		pass

	def _update_annotation_model(self, cursor, annotation_id, model):
		now = datetime.utcnow()
		sql = "UPDATE annotation SET stamp = %s, model = %s WHERE id = %s;"
		cursor.execute(sql, (now, model, annotation_id))

	@transactional
	def delete_annotations(self, image_id, domain):
		""" Removes all annotations for an image in a particular domain """
		pass

	def _delete_annotations(self, cursor, image_id, domain):
		sql = "DELETE FROM annotation WHERE domain = %s AND image_id = %s;"
		cursor.execute(sql, (domain, image_id))

	@transactional
	def delete_annotation(self, annotation_id):
		""" Removes a given annotation by id regardless of its domain/image """
		pass

	def _delete_annotation(self, cursor, annotation_id):
		sql = "DELETE FROM annotation WHERE id = %s;"
		cursor.execute(sql, (annotation_id,))

	@transactional
	def create_annotation(self, annotation, image_id):
		""" Stores the annotation in the database, setting its id """
		pass

	def _create_annotation(self, cursor, annotation, image_id):
		id = self._get_next_id(cursor, 'annotation')
		sql = "INSERT INTO annotation (id, image_id, stamp, boundary, domain, rank, model) VALUES (%s, %s, %s, %s, %s, %s, %s);"
		cursor.execute(sql, (id, image_id, annotation['stamp'], polygon_tuple_adapter(annotation['boundary']), annotation['domain'], annotation['rank'], annotation['model']))
		annotation['id'] = id

	@transactional
	def acquire_lock(self, image_id, domain, key, duration):
		"""
		Locks a particular image so that it is not served to other users while a
		user is creating annotations in a particular domain.  The duration is the
		amount of time in seconds the lock will be valid before expiring.  If a key
		is supplied, it will be used to create the lock.  Otherwise, a new key will
		be generated.

		If the lock already exists, its expiry will be updated using the new
		duration.

		A single key should be used for all locks acquired by a user.  This makes
		it easier to navigate.

		Throws an exception if the lock can't be acquired, otherwise it returns the
		key.  FIXME: Currently, a new lock can't be acquired for an image/domain
		until the old lock has been removed completely, even if it has expired.
		"""
		pass

	def _acquire_lock(self, cursor, image_id, domain, key, duration):
		expiry = datetime.utcnow() + timedelta(seconds=int(duration))
		if key:
			sql = "UPDATE image_lock SET expiry = %s WHERE image_id = %s AND domain = %s AND key = %s;"
			cursor.execute(sql, (expiry, image_id, domain, key))
			if cursor.rowcount > 0:
				return key
		else:
			key = uuid.uuid4().hex

		sql = "INSERT INTO image_lock (image_id, domain, key, expiry) VALUES (%s, %s, %s, %s);"
		cursor.execute(sql, (image_id, domain, key, expiry))
		return key

	@transactional
	def renew_lock(self, image_id, domain, key, duration):
		"""
		Renews an extant, unexpired lock on a given image + domain.
		Fails if the lock has expired or does not exist.

		Throws an exception if the lock can't be acquired, otherwise it returns the
		key.
		"""
		pass

	def _renew_lock(self, cursor, image_id, domain, key, duration):
		expiry = datetime.utcnow() + timedelta(seconds=int(duration))
		now = datetime.utcnow()
		sql = "UPDATE image_lock SET expiry = %s WHERE image_id = %s AND domain = %s AND key = %s AND expiry > %s;"
		cursor.execute(sql, (expiry, image_id, domain, key, now))
		if cursor.rowcount == 0:
			raise psycopg2.IntegrityError("Lock was not found or had expired")

	def _acquire_lock_atomic(self, cursor, domain, key, duration, query, parameters):
		"""
		Acquires a lock while querying for an available image at the same time.
		This method will return an (image_id, key) tuple, or will raise an
		exception if the key cannot be acquired.

		The query must return a single image ID, and all parameters must be
		supplied.
		"""
		expiry = datetime.utcnow() + timedelta(seconds=int(duration))
		if key:
			sql = "UPDATE image_lock SET expiry = %s WHERE image_id = (" + query + ") AND domain = %s AND key = %s RETURNING image_id;"
			params = [expiry, ]
			params.extend(parameters)
			params.append(domain)
			params.append(key)
			cursor.execute(sql, params)
			row = cursor.fetch_all()
			if cursor.rowcount > 0:
				return (row[0][0], key)
		else:
			key = uuid.uuid4().hex

		sql = "INSERT INTO image_lock (image_id, domain, key, expiry) VALUES ((" + query + "), %s, %s, %s) RETURNING image_id;"
		params = parameters
		params.append(domain)
		params.append(key)
		params.append(expiry)
		cursor.execute(sql, params)
		row = cursor.fetch_one()
		return (row[0], key)

	@transactional
	def release_lock(self, image_id, domain, key, checked):
		"""
		Releases a lock that was previously acquired, using the key.

		If checked is True, and the lock doesn't exist or it has already expired,
		then an IntegrityError will be raised.  This allows it to be used to
		invalidate inserts on expired locks.
		"""
		pass

	def _release_lock(self, cursor, image_id, domain, key, checked):
		now = datetime.utcnow()
		sql = "DELETE FROM image_lock WHERE image_id = %s AND domain = %s AND key = %s AND expiry > %s;"
		cursor.execute(sql, (image_id, domain, key, now))
		if checked and not cursor.rowcount > 0:
			raise psycopg2.IntegrityError("Lock was not found")

	@transactional
	def expire_locks(self):
		"""
		Removes all expired locks from the database.  This is meant to be run by a
		periodic process, not by end-users.
		"""
		pass

	def _expire_locks(self, cursor):
		now = datetime.utcnow()
		sql = "DELETE FROM image_lock WHERE expiry <= %s;"
		cursor.execute(sql, (now, ))
