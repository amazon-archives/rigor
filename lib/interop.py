"""
Tools for importing and exporting data from Rigor
"""

import rigor.logger
import rigor.database
import rigor.types
import rigor.hash
import rigor.utils
import rigor.s3

from datetime import datetime
from urlparse import urlsplit

import os
import stat
import json
import shutil
import errno
import mimetypes

#: The MIME type used when none is supplied, and guessing type fails
kDefaultMIMEType = 'application/octet-stream'

#: The file extension used when none is supplied, and type is not well-known
kDefaultExtension = 'dat'

class Importer(object):
	"""
	Imports percept metadata into the database, and copies files into the repository, if needed.

	:param config: Configuration data
	:type config: :py:class:`~rigor.config.RigorConfiguration` instance
	:param str database: Name of the database to export
	:param metadata: Name of the file containing metadata to read, or parsed metadata
	:param bool import_data: Whether to import percept data into the repository. This is highly recommended, and will be done by default.
	"""
	def __init__(self, config, database, metadata, import_data=True):
		self._config = config
		self._metadata = metadata
		self._import_data = import_data
		self._database = rigor.database.Database(database, config)
		self._logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self._s3 = None
		mimetypes.init()

	def run(self):
		"""
		Imports all percepts from the metadata file
		"""
		metadata = None
		if isinstance(self._metadata, list):
			metadata = self._metadata
		else:
			with open(self._metadata, 'rb') as metadata_file:
				metadata = json.load(metadata_file)
		for entry in metadata:
			self.import_percept(entry)

	def import_percept(self, metadata):
		"""
		Parses metadata and builds percept and annotations, then inserts it into the database. If file data is being imported, it will also copy the file data into the repository.

		:param dict metadata: Percept metadata, including annotations
		"""
		percept = rigor.types.Percept.deserialize(metadata)

		# We take control of the transaction here so we can fail if copying/moving the file fails
		with self._database.get_session() as session:
			session.add(percept)
			session.flush()
			with_data = ""
			if self._import_data:
				repository = urlsplit(percept.locator)
				if repository.scheme == 's3':
					if not self._s3 or self._s3.bucket != repository.netloc:
						self._s3 = rigor.s3.DefaultS3Client(self._config, repository.netloc, percept.credentials)
				source = metadata['source']
				destination = percept.locator
				with_data = " with data "
				self._copy_data(source, destination)
				source = urlsplit(source)
				if 'hash' not in metadata:
					percept.hash = rigor.hash.sha256_hash(source.path)
				if 'byte_count' not in metadata:
					percept.byte_count = os.path.getsize(source.path)
			self._logger.info("Imported percept ID {0}{1}".format(percept.id, with_data))
			return percept.id

	def _copy_data(self, source, destination):
		""" Copies file data from source path to destination """
		source = urlsplit(source)
		if source.netloc:
			raise NotImplementedError("Importing remote percept data is not implemented")
		destination = urlsplit(destination)
		if not destination.netloc:
			# Local
			rigor.utils.ensure_path_exists(os.path.dirname(destination.path))
			shutil.copy2(source.path, destination.path)
			os.chmod(destination.path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
		elif destination.scheme == 's3':
			self._s3.put(destination.path, source.path)
		else:
			raise NotImplementedError("Can't upload data to remote servers. Try local repository or S3")

class Exporter(object):
	"""
	Exports the data in a rigor database to a metadata file

	:param config: Configuration data
	:type config: :py:class:`~rigor.config.RigorConfiguration` instance
	:param str database: Name of the database to export
	:param str filename: Name of the file to write
	"""
	def __init__(self, config, database, filename):
		self._filename = filename
		self._config = config
		self._database = rigor.database.Database(database, config)

	def run(self, tag=None):
		"""
		Performs the export operation.

		:param str tag: If a tag is specified, exported percepts will be restricted to those with matching tag.
		"""
		with open(self._filename, 'wb') as out_file:
			with self._database.get_session(False) as session:
				query = session.query(rigor.types.Percept)
				if tag:
					query = query.join(rigor.types.PerceptTag).filter(rigor.types.PerceptTag.name == tag)
				first = True
				query.order_by(rigor.types.Percept.id)
				out_file.write('[\n')
				for percept in query.all():
					if first:
						first = False
					else:
						out_file.write(',\n')
					json.dump(percept.serialize(True), out_file, cls=rigor.utils.RigorJSONEncoder)
			out_file.write('\n]\n')
