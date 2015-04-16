""" Utilities for accessing data stored in Amazon S3 """

from abc import ABCMeta, abstractmethod
from io import BytesIO
from boto.s3.connection import S3Connection
from boto.s3.key import Key

class RigorS3Client(object):
	"""
	Object capable of accessing S3 data

	:param config: configuration data
	:type config: :py:class:`~rigor.config.RigorConfiguration`
	:param str bucket: S3 bucket containing data
	:param str credentials: name of credentials section
	"""
	__metaclass__ = ABCMeta

	def __init__(self, config, bucket, credentials=None):
		self._config = config
		self.bucket = bucket
		self._credentials = credentials

	@abstractmethod
	def get(self, key, local_file=None):
		"""
		Retrieves an object from S3

		:param str key: S3 key containing the data
		:param str local_file: path to a local file where data should be written, or :py:const:`None`.
		:return: data, unless a local file is given
		:rtype: file
		"""
		pass

	@abstractmethod
	def put(self, key, data):
		"""
		Uploads data to S3

		:param str key: S3 key where the data will go
		:param data: Either a file-like object, or a path to a destination file
		:type data: :py:class:`str` or :py:class:`file`
		"""
		pass

	@abstractmethod
	def delete(self, key):
		"""
		Removes data at the given key from S3

		:param str key: S3 key for the object to delete
		"""
		pass

	@abstractmethod
	def list(self, prefix=None):
		"""
		Lists the contents of the current S3 bucket

		:param str prefix: restrict listing to keys with this prefix
		:return: keys in the current bucket
		:rtype: list
		"""
		pass

class BotoS3Client(RigorS3Client):
	"""
	Object capable of accessing S3 data using Boto
	"""

	def __init__(self, config, bucket, credentials=None):
		super(BotoS3Client, self).__init__(config, bucket, credentials)
		connection_args = list()
		if credentials:
			connection_args.append(config.get(credentials, 'aws_access_key_id'))
			connection_args.append(config.get(credentials, 'aws_secret_access_key'))
		self._conn = S3Connection(*connection_args)
		self.bucket = self._conn.get_bucket(bucket)

	def get(self, key, local_file=None):
		""" See :py:meth:`RigorS3Client.get` """
		fetched_key = self.bucket.get_key(key)
		if fetched_key is None:
			return None
		if local_file is None:
			contents = BytesIO()
			fetched_key.get_file(contents)
			contents.seek(0)
			return contents
		else:
			fetched_key.get_contents_to_filename(local_file)

	def put(self, key, data):
		""" See :py:meth:`RigorS3Client.put` """
		remote_key = Key(self.bucket)
		remote_key.key = key
		if hasattr(data, 'read'):
			remote_key.set_contents_from_file(data)
		else:
			remote_key.set_contents_from_filename(data)

	def delete(self, key):
		""" See :py:meth:`RigorS3Client.delete` """
		remote_key = Key(self.bucket)
		remote_key.key = key
		remote_key.delete()

	def list(self, prefix=None):
		""" See :py:meth:`RigorS3Client.list` """
		if prefix is None:
			prefix = ""
		return self.bucket.list(prefix=prefix)

DefaultS3Client = BotoS3Client
