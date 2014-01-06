"""
Imports images into the database, populating it with metadata where
appropriate.  One-shot; an Importer should be created for each directory to be
imported.
"""

import rigor.logger
import rigor.database
import rigor.hash
import rigor.imageops

from rigor.dbmapper import DatabaseMapper
from rigor.config import config
from datetime import datetime

import os
import stat
import uuid
import json
import shutil
import errno
import imghdr

import psycopg2

class Importer(object):
	""" Class containing methods for importing images into the Rigor framework """

	extensions = ('jpg', 'png')

	modes = {'1': 1, 'L': 8, 'RGB': 24, 'RGBA': 32}

	def __init__(self, directory, database, move=False):
		"""
		directory is which directory to scan for files; move is whether to move
		files to the repository, as opposed to just copying them
		"""
		self._directory = directory
		self._logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self._move = move
		self._metadata = dict()
		self._database = rigor.database.Database(database)
		self._database_mapper = DatabaseMapper(self._database)
		try:
			import pyexiv2 # pylint: disable=W0612
		except ImportError:
			self._logger.warning("Unable to import pyexiv2; sensor data should be supplied in metadata")
		os.umask(002)

	def run(self):
		""" Imports all images from the directory, returning the number processed """
		metadata = self._read_global_metadata()
		for entry in os.listdir(self._directory):
			absfile = os.path.abspath(os.path.join(self._directory, entry))
			if not os.path.isfile(absfile):
				# Not a file
				continue
			(basename, sep, extension) = entry.rpartition(os.extsep)
			if not sep:
				# No separating dot
				self._logger.warn("Could not find separator for {0}".format(entry))
				continue
			if extension.lower() not in self.extensions:
				# Extension not in known list
				continue
			# Looks like we have an image file
			self.import_image(absfile, basename, metadata)

	def import_image(self, path, basename, metadata):
		""" Reads the metadata for an invididual image and returns an object ready to insert """
		image = dict()
		image['locator'] = uuid.uuid4().hex
		image['hash'] = rigor.hash.sha1_hash(path)

		data = rigor.imageops.read(path)
		image['resolution'] = (data.shape[1], data.shape[0])
		image['format'] = imghdr.what(path)
		if not image['format']:
			image['format'] = 'jpeg' # TODO: why is imghdr.what returning None for /home/kaolin/data/ICDAR2005SceneCompetition/wltang_15.08.2002/IMG_0001.JPG
		if len(data.shape) == 2:
			image['depth'] = 8
		else:
			image['depth'] = data.shape[2] * 8

		if not metadata:
			metadata = {};
		new_metadata = metadata.copy()
		new_metadata.update(self._read_local_metadata(basename))
		if 'timestamp' in new_metadata:
			image['stamp'] = datetime.strptime(new_metadata['timestamp'], config.get('import', 'timestamp_format'))
		else:
			image['stamp'] = datetime.utcfromtimestamp(os.path.getmtime(path))
		if 'source_id' in new_metadata:
			image['source_id'] = new_metadata['source_id']
		else:
			image['source_id'] = None

		image['tags'] = list()
		if 'tags' in new_metadata:
			image['tags'] = new_metadata['tags']
		has_sensor = False
		for tag in image['tags']:
			if tag.startswith('sensor:'):
				has_sensor = True
				break
		if not has_sensor:
			try:
				exif = pyexiv2.ImageMetadata(path) # pylint: disable=E0602
				exif.read()
				if 'Exif.Image.Make' in exif and 'Exif.Image.Model' in exif:
					sensor_tag = 'sensor:' + '_'.join((exif['Exif.Image.Make'].value, exif['Exif.Image.Model'].value))
					image['tags'] += sensor_tag.lower()
			except NameError:
				self._logger.warning("Image at {0}: No sensor listed in metadata, and EXIF data is not available.".format(path))

		if 'location' in new_metadata:
			image['location'] = new_metadata['location']
		else:
			image['location'] = None

		annotations = list()
		if 'annotations' in new_metadata:
			for annotation in new_metadata['annotations']:
				new_annotations = dict()
				for key in ('boundary', 'domain', 'model', 'confidence', 'annotation_tags'):
					if key in annotation:
						new_annotations[key] = annotation[key]
					else:
						new_annotations[key] = None
				if 'timestamp' in annotation:
					new_annotations['stamp'] = datetime.strptime(annotation['timestamp'], config.get('import', 'timestamp_format'))
				else:
					new_annotations['stamp'] = image['stamp']
				annotations.append(new_annotations)
		image['annotations'] = annotations

		destination = os.path.join(config.get('import', 'upload_repository'), image['locator'][0:2], image['locator'][2:4], os.extsep.join((image['locator'], image['format'])))
		# We take control of the transaction here so we can fail if copying/moving the file fails
		try:
			with self._database_mapper._db.get_cursor() as cursor: # pylint: disable=W0212
				self._database_mapper._create_image(cursor, image) # pylint: disable=W0212
				# Create destination directory, if it doesn't already exist.  try/except
				# structure avoids race condition
				try:
					os.makedirs(os.path.dirname(destination))
				except OSError as err:
					if err.errno == errno.EEXIST:
						pass
					else:
						raise
				if self._move:
					shutil.move(path, destination)
				else:
					shutil.copy2(path, destination)
				os.chmod(destination, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
				self._logger.info("Imported image {0}".format(image['locator']))
				return image
		except psycopg2.IntegrityError:
			self._logger.warn("The image at '{0}' already exists in the database".format(path))

	def _read_local_metadata(self, basename):
		""" Reads the metadata file for the image and sets defaults """
		metadata_file = os.path.join(self._directory, "{0}.json".format(basename))
		if not os.path.isfile(metadata_file):
			return dict()
		with open(metadata_file, 'r') as metadata:
			return json.load(metadata)

	def _read_global_metadata(self):
		""" Reads the metadata file for the image directory and sets defaults """
		metadata_file = os.path.join(self._directory, config.get('import', 'metadata_file'))
		if not os.path.isfile(metadata_file):
			return
		with open(metadata_file, 'r') as metadata:
			return json.load(metadata)
