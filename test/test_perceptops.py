from rigor.perceptops import PerceptOps, ImageOps
from rigor.types import Percept
from s3 import setup_module, teardown_module, kKeys
import rigor.config
import shutil
import os.path
import constants
import db
import pytest

kConfig = rigor.config.RigorDefaultConfiguration(constants.kConfigFile)

def test_init():
	ops = PerceptOps(kConfig)

def test_fetch():
	ops = PerceptOps(kConfig)
	def read(locator, credentials):
		return (locator, credentials)
	ops.read = read
	percept = Percept()
	percept.locator = constants.kExampleTextFile
	result = ops.fetch(percept)
	assert result == (percept.locator, None)

def test_read_local():
	ops = PerceptOps(kConfig)
	result = ops.read(constants.kExampleTextFile, None)
	with result as text_file:
		assert text_file.read() == 'This is a file to test uploading a file to S3'

def test_read_local_file_uri():
	ops = PerceptOps(kConfig)
	result = ops.read('file://' + constants.kExampleTextFile, None)
	with result as text_file:
		assert text_file.read() == 'This is a file to test uploading a file to S3'

def test_read_s3():
	ops = PerceptOps(kConfig)
	result = ops.read('s3://' + os.path.join(constants.kExampleBucket, kKeys[0]), None)
	with result as text_file:
		assert text_file.read() == '0'

def test_read_http():
	ops = PerceptOps(kConfig)
	result = ops.read('http://' + os.path.join(constants.kExampleBucket + '.' + constants.kS3HostName, kKeys[1]), None)
	with result as text_file:
		assert text_file.read() == '1'

def test_remove_local():
	shutil.copy(constants.kExampleImageFile, constants.kExampleTemporaryImageFile)
	assert os.path.exists(constants.kExampleTemporaryImageFile)
	ops = PerceptOps(kConfig)
	ops.remove(constants.kExampleTemporaryImageFile)
	assert not os.path.exists(constants.kExampleTemporaryImageFile)

def test_remove_s3():
	ops = PerceptOps(kConfig)
	assert ops.read('s3://' + os.path.join(constants.kExampleBucket, kKeys[0]), None) is not None
	ops.remove('s3://' + os.path.join(constants.kExampleBucket, kKeys[0]), None)
	assert ops.read('s3://' + os.path.join(constants.kExampleBucket, kKeys[0]), None) is None

def test_remove_http():
	ops = PerceptOps(kConfig)
	with pytest.raises(NotImplementedError):
		ops.remove('http://' + os.path.join(constants.kExampleBucket + '.' + constants.kS3HostName, kKeys[1]), None)

def test_delete_local():
	shutil.copy(constants.kExampleImageFile, constants.kExampleTemporaryImageFile)
	assert os.path.exists(constants.kExampleTemporaryImageFile)
	database = db.get_database()
	ops = PerceptOps(kConfig)
	with database.get_session() as session:
		percept = session.query(rigor.types.Percept).get(642924)
		percept.locator = 'file://' + constants.kExampleTemporaryImageFile
		ops.destroy(percept, session)
	assert not os.path.exists(constants.kExampleTemporaryImageFile)

def test_delete_local_by_id():
	shutil.copy(constants.kExampleImageFile, constants.kExampleTemporaryImageFile)
	assert os.path.exists(constants.kExampleTemporaryImageFile)
	database = db.get_database()
	ops = PerceptOps(kConfig)
	with database.get_session() as session:
		percept = session.query(rigor.types.Percept).get(642924)
		percept.locator = 'file://' + constants.kExampleTemporaryImageFile
		ops.destroy(percept.id, session)
	assert not os.path.exists(constants.kExampleTemporaryImageFile)

try:
	import cv2

	def test_imageops_fetch():
		ops = ImageOps(kConfig)
		percept = Percept()
		percept.locator = constants.kExampleImageFile
		result = ops.fetch(percept)
		assert result.shape == constants.kExampleImageDimensions

	def test_imageops_decode():
		ops = ImageOps(kConfig)
		result = ops.decode(constants.kExampleImageFile)
		assert result.shape == constants.kExampleImageDimensions

except ImportError:
	pass
