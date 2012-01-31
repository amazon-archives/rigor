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

import psycopg2

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
		try:
			import pyexiv2
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
		image['hash'] = rigor.hash.hash(path)

		data = rigor.imageops.read(path)
		image['resolution'] = data.size
		image['format'] = data.format.lower()
		image['depth'] = Importer.modes[data.mode]

		md = metadata.copy()
		md.update(self._read_local_metadata(basename))
		if 'timestamp' in md:
			image['stamp'] = datetime.strptime(md['timestamp'], config.get('import', 'timestamp_format'))
		else:
			image['stamp'] = datetime.utcfromtimestamp(os.path.getmtime(path))

		if 'sensor' in md:
			image['sensor'] = md['sensor']
		else:
			try:
				exif = pyexiv2.ImageMetadata(path)
				exif.read()
				if 'Exif.Image.Make' in exif and 'Exif.Image.Model' in exif:
					image['sensor'] = ' '.join((exif['Exif.Image.Make'].value, exif['Exif.Image.Model'].value))
			except NameError:
				self._logger.warning("Image at {0}: No sensor listed in metadata, and EXIF data is not available; sensor will be null.".format(path))
				image['sensor'] = None

		for key in ('location', 'source', 'tags'):
			if key in md:
				image[key] = md[key]
			else:
				image[key] = None

		annotations = list()
		if 'annotations' in md:
			for annotation in md['annotations']:
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

		destination = os.path.join(config.get('import', 'upload_repository'), image['locator'][0:2], image['locator'][2:4], os.extsep.join((image['locator'], image['format'])))
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
			os.chmod(destination, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
			self._database_mapper._db.commit(cursor)
			self._logger.info("Imported image {0}".format(image['locator']))
			return image
		except psycopg2.IntegrityError as e:
			self._database_mapper._db.rollback(cursor)
			self._logger.warn("The image at '{0}' already exists in the database".format(path))
		except:
			self._database_mapper._db.rollback(cursor)
			raise

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
