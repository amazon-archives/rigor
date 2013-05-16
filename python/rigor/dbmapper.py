""" Mappings between logical operations and database queries """

from rigor.database import transactional, RowMapper, uuid_transform, polygon_transform, polygon_tuple_adapter

import uuid
from datetime import datetime, timedelta
import psycopg2

def resolution_transform(value, _column_name, row):
	"""
	Turns the x_resolution and y_resolution database columns into a single tuple
	for use as a resolution
	"""
	if value is None:
		return None
	return (row['x_resolution'], row['y_resolution'])

kImageMapper = RowMapper(field_mappings={'x_resolution': 'resolution', 'y_resolution': None}, field_transforms={'locator':uuid_transform, 'resolution':resolution_transform})
kAnnotationMapper = RowMapper(field_transforms={'boundary':polygon_transform})

class DatabaseMapper(object):
	""" Reads and write Images to database """
	# pylint: disable=R0201

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
		sql = "SELECT id, locator, hash, stamp, x_resolution, y_resolution, format, depth, location FROM image WHERE id = %s;"
		cursor.execute(sql, (image_id, ))
		image = cursor.fetch_only_one(kImageMapper)
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
	def get_image_for_analysis(self, domain, image_id):
		"""
		Retrieves an image for the domain from the database, used for
		algorithm analysis, and associated annotations
		"""
		pass

	def _get_image_for_analysis(self, cursor, domain, image_id):
		sql = "SELECT * FROM (SELECT image.id, image.locator, image.hash, image.stamp, image.x_resolution, image.y_resolution, image.format, image.depth, FROM annotation LEFT JOIN image ON annotation.image_id = image.id WHERE annotation.domain = %s) image WHERE image.id = %s GROUP BY image.id, image.locator, image.hash, image.stamp, image.x_resolution, image.y_resolution, image.format, image.depth"
		cursor.execute(sql, (domain, image_id))
		row = cursor.fetch_only_one()
		image = kImageMapper.map_row(row)
		sql = "SELECT id, model, boundary FROM annotation WHERE image_id = %s AND domain = %s;"
		cursor.execute(sql, (row[0], domain, ))
		image['annotations'] = cursor.fetch_all(kAnnotationMapper)
		return image

	@transactional
	def get_images_for_analysis(self, domain, limit=None, random=False, tags_require=None, tags_exclude=None):
		"""
		Retrieves all images for the domain from the database, used for
		algorithm analysis.  The optional limit limits the number of
		images returned.  If random, the images will be randomly selected.
		Otherwise, images will be returned sorted by ID.
		"""
		pass

	def _get_images_for_analysis(self, cursor, domain, limit, random, tags_require=None, tags_exclude=None): # pylint: disable=R0914
		args = []
		sql = "SELECT image.* FROM image "
		where = ""
		# logic roughly from stackoverflow:
		# http://stackoverflow.com/a/602892/856925
		if tags_exclude or tags_require:
			tagcount = 0
			if tags_require:
				for tag_require in tags_require:
					tagstring = "t"+str(tagcount)
					sql += "INNER JOIN tag "+tagstring+" ON "+tagstring+".image_id = image.id AND "+tagstring+".name=%s "
					args.append(tag_require)
					tagcount += 1
			if tags_exclude:
				for tag_exclude in tags_exclude:
					tagstring = "t"+str(tagcount)
					sql += "LEFT OUTER JOIN tag "+tagstring+" ON "+tagstring+".image_id = image.id AND "+tagstring+".name=%s "
					where += "AND "+tagstring+" IS NULL "
					args.append(tag_exclude)
					tagcount += 1
		where = "INNER JOIN annotation ON annotation.image_id = image.id AND annotation.domain = %s " + where
		args.append(domain,)
		where += " GROUP BY image.id"
		if random and limit:
			where += " ORDER BY random()"
		else:
			where += " ORDER BY image.id"
		if limit:
			where += " LIMIT %s"
			args.append(limit,)

		sql = sql + where
		cursor.execute(sql, args)
		rows = cursor.fetch_all()
		images = list()
		for row in rows:
			image = kImageMapper.map_row(row)
			sql = "SELECT id, model, boundary FROM annotation WHERE image_id = %s AND domain = %s;"
			cursor.execute(sql, (row[0], domain, ))
			image['annotations'] = cursor.fetch_all(kAnnotationMapper)
			images.append(image)
		return images

	@transactional
	def get_tags_by_image_id(self, image_id):
		"""
		Retrieves all tags for a given image
		"""
		pass

	def _get_tags_by_image_id(self, cursor, image_id):
		sql = "SELECT name FROM tag where image_id = %s;"
		cursor.execute(sql, (image_id, ))
		rows = cursor.fetch_all()
		return (row[0] for row in rows)

	@transactional
	def create_image(self, image):
		""" Stores the image metadata in the database, setting its id """
		pass

	def _create_image(self, cursor, image):
		image_id = self._get_next_id(cursor, 'image')
		sql = "INSERT INTO image (id, locator, hash, stamp, x_resolution, y_resolution, format, depth, location) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
		location = None
		if image['location']:
			location = "({0},{1})".format(image['location'][0], image['location'][1])
		cursor.execute(sql, (image_id, image['locator'], image['hash'], image['stamp'], image['resolution'][0], image['resolution'][1], image['format'], image['depth'], location))
		image['id'] = image_id
		if image['tags']:
			self._create_tags(cursor, image['tags'], image_id)
		if image['annotations']:
			for annotation in image['annotations']:
				self._create_annotation(cursor, annotation, image_id)

	def _create_tags(self, cursor, tags, image_id):
		if hasattr(tags, 'upper'):
			# tags is a string, change to list
			tags = (tags,)
		sql = "INSERT INTO tag (image_id, name) VALUES (%s, %s);"
		cursor.executemany(sql, ((image_id, tag) for tag in tags))

	def _delete_tags(self, cursor, tags, image_id):
		if hasattr(tags, 'upper'):
			#tags is a string, change to list
			tags = (tags, )
		sql = "DELETE FROM tag WHERE image_id = %s AND name = %s;"
		cursor.executemany(sql, ((image_id, tag) for tag in tags))

	@transactional
	def get_annotation_by_id(self, annotation_id):
		""" Retrieves the annotation from the database """
		pass

	def _get_annotation_by_id(self, cursor, annotation_id):
		sql = "SELECT id, confidence, stamp, boundary, domain, model FROM annotation WHERE id = %s;"
		cursor.execute(sql, (annotation_id, ))
		return cursor.fetch_only_one(kAnnotationMapper)

	def _get_annotations_by_image_id(self, cursor, image_id):
		sql = "SELECT id, confidence, stamp, boundary, domain, model FROM annotation WHERE image_id = %s;"
		cursor.execute(sql, (image_id, ))
		return cursor.fetch_all(kAnnotationMapper)

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
		image_id = self._get_next_id(cursor, 'annotation')
		sql = "INSERT INTO annotation (id, image_id, confidence, stamp, boundary, domain, model) VALUES (%s, %s, %s, %s, %s, %s);"
		cursor.execute(sql, (image_id, image_id, annotation['confidence'], annotation['stamp'], polygon_tuple_adapter(annotation['boundary']), annotation['domain'], annotation['model']))
		annotation['id'] = image_id
		if 'annotation_tags' in annotation and annotation['annotation_tags']:
			self._create_annotation_tags(cursor, annotation['annotation_tags'], image_id)

	def _create_annotation_tags(self, cursor, annotation_tags, annotation_id):
		sql = "INSERT INTO annotation_tag (annotation_id, name) VALUES (%s, %s);"
		cursor.executemany(sql, ((annotation_id, tag) for tag in annotation_tags))

	@transactional
	def get_annotation_tags_by_annotation_id(self, annotation_id):
		""" returns all the annotation tags for a given annotation  """
		pass

	def _get_annotation_tags_by_annotation_id(self, cursor, annotation_id):
		sql = "SELECT name FROM annotation_tag where annotation_id = %s;"
		cursor.execute(sql, (annotation_id, ))
		rows = cursor.fetch_all()
		return (row[0] for row in rows)

	@transactional
	def patch(self, patch, patch_level):
		"""
		Patches the database by running all commands in the patch file (a file-like
		object or string containing the file's contents), then updating the patch
		table to reflect the changes.  NOTE: the patch file should not contain any
		transaction begin or end commands.
		"""

	def _patch(self, cursor, patch, patch_level):
		if hasattr(patch, 'read'):
			patch = patch.read()
		cursor.execute(patch)
		sql = "UPDATE meta SET value=%s WHERE key=%s;"
		cursor.execute(sql, (patch_level, 'patch_level'))
		if cursor.rowcount == 0:
			raise psycopg2.IntegrityError("Could not update patch level")

	@transactional
	def get_patch_level(self):
		""" Gets the database's current patch level """

	def _get_patch_level(self, cursor):
		sql = "SELECT value FROM meta WHERE key='patch_level';"
		cursor.execute(sql)
		row = cursor.fetch_only_one()
		return int(row[0])

	@transactional
	def get_destroy_lock(self):
		""" Gets whether the database can be destroyed from the command line """

	def _get_destroy_lock(self, cursor):
		sql = "SELECT 1 FROM meta WHERE key=%s AND value=%s::text;"
		cursor.execute(sql, ('destroy_lock', True))
		return cursor.rowcount != 0

	@transactional
	def set_destroy_lock(self, locked):
		""" Sets whether the database can be destroyed from the command line """

	def _set_destroy_lock(self, cursor, locked):
		sql = "UPDATE meta SET value = %s WHERE key = %s;"
		cursor.execute(sql, (locked, 'destroy_lock'))
		sql = "INSERT INTO meta (key, value) SELECT %s, %s WHERE NOT EXISTS (SELECT 1 FROM meta WHERE key=%s);"
		cursor.execute(sql, ('destroy_lock', locked, 'destroy_lock'))

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
