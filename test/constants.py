import datetime
import os.path

kDirName, filename = os.path.split(os.path.abspath(__file__))
kFixtureFile = os.path.join(kDirName, 'types.db')
kTestFile = os.path.join(kDirName, 'test.db')
kTestDirectory = os.path.join(kDirName, 'tempdir', 'child')
kConfigFile = os.path.join(kDirName, 'testing.ini')
kConfigFile2 = os.path.join(kDirName, 'testing2.ini')
kLockFile = os.path.join(kDirName, 'lockfile')
kAwsBucket = 'orion.aws.testing'
kImportFile = os.path.join(kDirName, 'import.json')
kImportDirectory = os.path.join(kDirName, 'to_import')
kRepoDirectory = os.path.join(kDirName, 'imported')
kImportDatabase = os.path.join(kDirName, 'imported.db')
kExampleTextFile = os.path.join(kDirName, 'example_text_file.txt')
kExampleImageFile = os.path.join(kDirName, 'example_image.png')
kExampleTemporaryImageFile = os.path.join(kDirName, 'example_image_temp.png')
kExampleDownloadedFile = os.path.join(kDirName, 'fetched.dat')
kExampleCheckpointFile = os.path.join(kDirName, 'example_checkpoint.dat')
kExampleNewCheckpointFile = os.path.join(kDirName, 'example_new_checkpoint.dat')
kS3HostName = 's3.amazonaws.com'
kExampleBucket = 'rigor-test-bucket'
kExampleCredentials = 'test_credentials'
kExampleImageDimensions = (1080, 3840, 3)
kNonexistentFile = '/xxxzzfooxxx'
kExamplePercept = {
	'annotations': [
		{'boundary': ((1, 10), (3, 6), (1, 10), (10, 3)), 'confidence': 4, 'domain': u'test', 'model': u'e', 'properties': {u'prop': u'value'}, 'stamp': datetime.datetime(2015, 2, 3, 20, 16, 7, 252667), 'tags': [ u'test_tag', ]},
  {'boundary': ((10, 4), (4, 8), (3, 8), (6, 3)), 'confidence': 5, 'domain': u'test', 'model': u'e', 'stamp': datetime.datetime(2015, 2, 3, 20, 16, 7, 252787)},
  {'boundary': ((1, 7), (1, 9), (7, 1), (3, 5)), 'confidence': 4, 'domain': u'test', 'model': u'd', 'stamp': datetime.datetime(2015, 2, 3, 20, 16, 7, 252969)}
	],
	'device_id': u'device_1938401',
	'format': u'image/jpeg',
	'hash': u'edd66afcf0eb4f5ef392fd8e94ff0ff2139ddc01',
	'locator': u'example://mybucket/182828291',
	'properties': {u'val1': u'val2'},
	'sensors': {'acceleration_x': 0.1, 'acceleration_y': 0.2, 'acceleration_z': 0.3, 'altitude': 123.0, 'altitude_accuracy': 2.34, 'bearing': 180.1, 'bearing_accuracy': 1.23, 'location': (34.56, -120.2), 'location_accuracy': 0.1, 'location_provider': u'gps', 'speed': 60.1},
	'stamp': datetime.datetime(2015, 2, 3, 20, 16, 7, 252487),
	'x_size': 800, 'y_size': 600
}
