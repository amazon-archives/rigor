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
from psycopg2 import IntegrityError

import pyexiv2

import os
import uuid
import json
import shutil
import errno

class Importer(object):
	""" Class containing methods for importing images into the Rigor framework """

	extensions = ('jpg', 'png')
	""" List of file extensions to scan """

	modes = {'1': 1, 'L': 8, 'RGB': 24, 'RGBA': 32}

	def __init__(self, directory, move=False):
		"""
		directory is which directory to scan for files; move is whether to move
		files to the repository, as opposed to just copying them
		"""
		self._directory = directory
		self._logger = rigor.logger.getLogger('.'.join((__name__, self.__class__.__name__)))
		self._move = move
		self._metadata = dict()
		self._database = rigor.database.Database()
		self._database_mapper = DatabaseMapper(self._database)

	def run(self):
		""" Imports all images from the directory, returning the number processed """
		self._read_global_metadata()
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
			self._import_image(absfile, basename)

	def _import_image(self, path, basename):
		""" Reads the metadata for an invididual image and returns an object ready to insert """
		image = dict()
		image['locator'] = uuid.uuid4().hex
		image['hash'] = rigor.hash.hash(path)

		data = rigor.imageops.read(path)
		image['resolution'] = data.size
		image['format'] = data.format.lower()
		image['depth'] = Importer.modes[data.mode]

		metadata = self._metadata.copy()
		metadata.update(self._read_local_metadata(basename))
		if 'timestamp' in metadata:
			image['stamp'] = datetime.strptime(metadata['timestamp'], config.get('import', 'timestamp_format'))
		else:
			image['stamp'] = datetime.utcfromtimestamp(os.path.getmtime(path))

		if 'sensor' in metadata:
			image['sensor'] = metadata['sensor']
		else:
			exif = pyexiv2.ImageMetadata(path)
			exif.read()
			if 'Exif.Image.Make' in exif and 'Exif.Image.Model' in exif:
				image['sensor'] = ' '.join((exif['Exif.Image.Make'].value, exif['Exif.Image.Model'].value))

		for key in ('location', 'source', 'tags'):
			if key in metadata:
				image[key] = metadata[key]
			else:
				image[key] = None

		annotations = list()
		if 'annotations' in metadata:
			for annotation in metadata['annotations']:
				a = dict()
				for key in ('boundary', 'domain', 'rank', 'model'):
					if key in annotation:
						a[key] = annotation[key]
					else:
						a[key] = None
				if 'timestamp' in annotation:
					a['stamp'] = datetime.strptime(annotation['timestamp'], config.get('import', 'timestamp_format'))
				else:
					a['stamp'] = image['stamp']
				annotations.append(a)
		image['annotations'] = annotations

		destination = os.path.join(config.get('global', 'image_repository'), image['locator'][0:2], image['locator'][2:4], os.extsep.join((image['locator'], image['format'])))
		# We take control of the transaction here so we can fail if copying/moving the file fails
		cursor = self._database_mapper._db.get_cursor()
		try:
			self._database_mapper._create_image(cursor, image)
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
			self._database_mapper._db.commit(cursor)
			self._logger.info("Imported image {0}".format(image['locator']))
			return image
		except IntegrityError as e:
			self._database_mapper._db.rollback(cursor)
			self._logger.warn("The image at '{0}' already exists in the database".format(path))
		except:
			self._database_mapper._db.rollback(cursor)
			raise

	def _read_local_metadata(self, basename):
		""" Reads the metadata file for the image and sets defaults """
		metadata_file = "{0}.json".format(basename)
		if not os.path.isfile(metadata_file):
			return dict()
		return json.load(open(metadata_file, 'r'))

	def _read_global_metadata(self):
		""" Reads the metadata file for the image directory and sets defaults """
		metadata_file = os.path.join(self._directory, config.get('import', 'metadata_file'))
		if not os.path.isfile(metadata_file):
			return
		self._metadata = json.load(open(metadata_file, 'r'))

