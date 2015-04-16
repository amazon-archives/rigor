from rigor.s3 import RigorS3Client, BotoS3Client
from rigor.config import RigorDefaultConfiguration
from s3 import setup_module, teardown_module, kKeys
import pytest
import constants
import os

kConfig = RigorDefaultConfiguration(constants.kConfigFile)

class DummyS3Client(RigorS3Client):
	""" Coverage of abstract methods """
	def get(self, key, local_file=None):
		return RigorS3Client.get(self, key, local_file)
	def put(self, key, data):
		return RigorS3Client.put(self, key, data)
	def delete(self, key):
		return RigorS3Client.delete(self, key)
	def list(self, prefix=None):
		return RigorS3Client.list(self, prefix)

@pytest.fixture
def client():
	return BotoS3Client(kConfig, constants.kExampleBucket)

def test_dummy():
	dummy = DummyS3Client(kConfig, constants.kExampleBucket)
	dummy.get(kKeys[0])
	dummy.put(kKeys[0], 'test')
	dummy.delete(kKeys[0])
	dummy.list()

def test_init_client(client):
	assert client is not None

def test_init_client_with_credentials():
	client = BotoS3Client(kConfig, constants.kExampleBucket, constants.kExampleCredentials)

def test_get_open_file(client):
	for index, key in enumerate(kKeys):
		with client.get(key) as contents:
			value = contents.read()
			assert value == str(index)

def test_get_missing(client):
	contents = client.get('xthanteohntahoeaoedhaod')
	assert contents is None

def test_get_local_file(client):
	client.get(kKeys[0], constants.kExampleDownloadedFile)
	with open(constants.kExampleDownloadedFile, 'rb') as data:
		assert data.read() == str(0)

def test_put_local_filename(client):
	key = 'new-s3-key-4'
	with open(constants.kExampleTextFile, 'rb') as text_file:
		text = text_file.read()
	client.put(key, constants.kExampleTextFile)
	with client.get(key) as contents:
		assert contents.read() == text

def test_put_local_open_file(client):
	key = 'new-s3-key-5'
	with open(constants.kExampleTextFile, 'rb') as text_file:
		text = text_file.read()
		text_file.seek(0)
		client.put(key, text_file)
	with client.get(key) as contents:
		assert contents.read() == text

def test_delete(client):
	key = 'new-s3-key-6'
	client.put(key, constants.kExampleTextFile)
	assert client.get(key) is not None
	client.delete(key)
	assert client.get(key) is None

def test_list(client):
	count = 0
	for item in client.list():
		count += 1
	assert count >= 3

def test_list_prefix(client):
	count = 0
	for item in client.list('s3-key'):
		count += 1
		assert item.key in kKeys
	assert count == 3
