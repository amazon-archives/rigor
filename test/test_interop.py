import os
import json
import constants
import shutil
import db
from s3 import setup_module, teardown_module
from datetime import datetime
from urlparse import urlsplit
from rigor.config import RigorDefaultConfiguration
from rigor.database import Database
from rigor.utils import RigorJSONEncoder
from rigor.interop import Importer, Exporter
from rigor.types import Percept
from rigor.perceptops import PerceptOps
import pytest

kConfig = RigorDefaultConfiguration(constants.kConfigFile)

@pytest.fixture
def importdb():
	shutil.copyfile(constants.kFixtureFile, constants.kImportDatabase)
	database = Database(constants.kImportDatabase, kConfig)
	with database.get_session() as session:
		session.query(Percept).delete()
	return database

@pytest.fixture
def exportdb():
	return db.get_database()

def setup_function(function):
	teardown_function(function)
	os.mkdir(constants.kRepoDirectory)
	os.mkdir(constants.kImportDirectory)
	percepts = list()
	for count in range(1, 4):
		data_filename = '{:02}.txt'.format(count)
		data_path = os.path.abspath(os.path.join(constants.kImportDirectory, data_filename))
		repo_path = os.path.abspath(os.path.join(constants.kRepoDirectory, data_filename))
		with open(data_path, 'w') as data_file:
			data_file.write(str(count))
		percept = {
			'source' : 'file://' + data_path,
			'locator': 'file://' + repo_path,
			'stamp': datetime.utcnow(),
			'format': 'text/plain',
			'tags': [ 'unittest', ],
			'annotations': [{
				'domain': 'unittest',
				'confidence': 5,
				'model': str(count),
			}]
		}
		percepts.append(percept)
		with open(constants.kImportFile, 'w') as import_file:
			json.dump(percepts, import_file, cls=RigorJSONEncoder)

def teardown_function(function):
	shutil.rmtree(constants.kRepoDirectory, True)
	shutil.rmtree(constants.kImportDirectory, True)
	try:
		os.unlink(constants.kImportFile)
	except OSError:
		pass
	try:
		os.unlink(constants.kImportDatabase)
	except OSError:
		pass

def test_setup():
	# Silly, but the setup's complicated enough
	assert len(os.listdir(constants.kRepoDirectory)) == 0
	assert len(os.listdir(constants.kImportDirectory)) == 3
	assert os.path.exists(constants.kImportFile)

def test_import_single_percept(importdb):
	importer = Importer(kConfig, constants.kImportDatabase, constants.kImportFile, import_data=False)
	with importdb.get_session() as session:
		percepts = session.query(Percept).all()
		assert len(percepts) == 0
	percept_id = importer.import_percept(constants.kExamplePercept)
	assert percept_id > 0
	with importdb.get_session() as session:
		percepts = session.query(Percept).all()
		assert len(percepts) == 1

def test_import_non_writable_dir(importdb):
	source_path = os.path.abspath(os.path.join(constants.kImportDirectory, '01.txt'))
	metadata = {
		'source' : 'file://' + source_path,
		'locator': 'file:////xyz/01.txt',
		'format': 'text/plain',
		}
	importer = Importer(kConfig, constants.kImportDatabase, None, import_data=True)
	with pytest.raises(OSError):
		importer.import_percept(metadata)

def test_import_all_no_data(importdb):
	importer = Importer(kConfig, constants.kImportDatabase, constants.kImportFile, import_data=False)
	importer.run()
	with importdb.get_session() as session:
		percepts = session.query(Percept).all()
		assert len(percepts) == 3
		for percept in percepts:
			locator = urlsplit(percept.locator)
			assert not os.path.exists(locator.path)
			assert len(percept.annotations) == 1

def test_import_all_with_data(importdb):
	importer = Importer(kConfig, constants.kImportDatabase, constants.kImportFile, import_data=True)
	importer.run()
	with importdb.get_session() as session:
		percepts = session.query(Percept).all()
		assert len(percepts) == 3
		for percept in percepts:
			locator = urlsplit(percept.locator)
			assert os.path.exists(locator.path)
			assert len(percept.annotations) == 1
		assert percepts[0].hash == '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b'
		assert percepts[1].hash == 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35'
		assert percepts[2].hash == '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce'

def test_import_all_with_data_to_s3(importdb):
	with open(constants.kImportFile, 'rb') as import_file:
		metadata = json.load(import_file)
	for index, percept in enumerate(metadata):
		percept['locator'] = 's3://' + os.path.join(constants.kExampleBucket, str(index) + ".txt")
	importer = Importer(kConfig, constants.kImportDatabase, metadata, import_data=True)
	importer.run()
	ops = PerceptOps(kConfig)
	with importdb.get_session() as session:
		percepts = session.query(Percept).all()
		assert len(percepts) == 3
		for percept in percepts:
			assert ops.read(percept.locator) is not None
			locator = urlsplit(percept.locator)
			assert len(percept.annotations) == 1

def test_import_all_with_data_to_remote(importdb):
	with open(constants.kImportFile, 'rb') as import_file:
		metadata = json.load(import_file)
	for index, percept in enumerate(metadata):
		percept['locator'] = 'http://' + os.path.join(constants.kExampleBucket + '.' + constants.kS3HostName, str(index) + ".txt")
	importer = Importer(kConfig, constants.kImportDatabase, metadata, import_data=True)
	with pytest.raises(NotImplementedError):
		importer.run()

def test_import_remote_with_data(importdb):
	metadata = [{
		'source' : 'http://test_url',
		'locator': 'file://' + constants.kRepoDirectory,
		'format': 'text/plain',
		}]
	importer = Importer(kConfig, constants.kImportDatabase, metadata, import_data=True)
	with pytest.raises(NotImplementedError):
		importer.run()

def test_export(exportdb):
	exporter = Exporter(kConfig, constants.kTestFile, constants.kImportFile)
	exporter.run()
	with open(constants.kImportFile, 'rb') as import_file:
		metadata = json.load(import_file)
		assert len(metadata) == 12
		assert metadata[0]['device_id'] == 'device_1938401'
		assert metadata[0]['annotations'][0]['model'] == 'b'

def test_export_tag(exportdb):
	exporter = Exporter(kConfig, constants.kTestFile, constants.kImportFile)
	exporter.run('simple')
	with open(constants.kImportFile, 'rb') as import_file:
		metadata = json.load(import_file)
		assert len(metadata) == 3
