from rigor.utils import RigorJSONEncoder, parse_timestamp, ensure_path_exists
from datetime import datetime
import json
import pytest
import constants
import os.path
import shutil

def test_json_encoder_date():
	result = json.dumps({'a': 1, 'b': 2, 'c': '3', 'd': datetime(2015, 3, 17, 22, 37, 33, 29292), 'e': (1, 2), 'f': [3,3], 'g': {'h': 'i'}}, cls=RigorJSONEncoder)
	assert result == '{"a": 1, "c": "3", "b": 2, "e": [1, 2], "d": "2015-03-17T22:37:33.029292Z", "g": {"h": "i"}, "f": [3, 3]}'

def test_json_encoder_custom():
	with pytest.raises(TypeError) as error:
		json.dumps(str, cls=RigorJSONEncoder)

def test_parse_timestamp():
	timestamp = parse_timestamp('2013-08-24T23:17:56Z')
	assert timestamp == datetime(2013, 8, 24, 23, 17, 56)

def test_parse_timestamp_fractional():
	timestamp = parse_timestamp('2013-08-24T03:17:56.242421Z')
	assert timestamp == datetime(2013, 8, 24, 3, 17, 56, 242421)

def test_parse_timestamp_timestamp():
	dt = datetime(2013, 8, 24, 3, 17, 56, 242421)
	timestamp = parse_timestamp(dt)
	assert timestamp == dt

def test_parse_timestamp_invalid():
	with pytest.raises(ValueError):
		parse_timestamp('zz')

def test_ensure_path_exists():
	if os.path.exists(constants.kTestDirectory):
		shutil.rmtree(constants.kTestDirectory)
	ensure_path_exists(constants.kTestDirectory)
	assert os.path.exists(constants.kTestDirectory)
	shutil.rmtree(constants.kTestDirectory)

def test_ensure_path_exists_no_permission():
	with pytest.raises(OSError):
		ensure_path_exists('/xxxxx/yyyy')

def test_ensure_path_exists_exists():
	ensure_path_exists(constants.kTestDirectory)
	assert os.path.exists(constants.kTestDirectory)
	ensure_path_exists(constants.kTestDirectory)
	shutil.rmtree(constants.kTestDirectory)
