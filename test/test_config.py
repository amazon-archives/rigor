import pytest
import shutil
import constants
import os.path
import rigor.config

@pytest.fixture
def config():
	return rigor.config.RigorDefaultConfiguration(constants.kConfigFile)

def test_get_config_default_path():
	rigor.config.RigorDefaultConfiguration() is not None

def test_get_config_multiple_files():
	assert rigor.config.RigorDefaultConfiguration(constants.kConfigFile, constants.kConfigFile2) is not None

def test_get_config_nonexistent_path():
	rigor.config.RigorDefaultConfiguration(constants.kNonexistentFile) is not None

def test_get_config_test_path(config):
	assert config is not None

def test_get_config_default_value(config):
	assert config.get('import', 'hash_imports')

def test_get_config_boolean(config):
	assert config.getboolean('import', 'hash_imports') is True

def test_get_config_bad_boolean(config):
	with pytest.raises(ValueError) as error:
		config.getboolean('database', 'driver')
		assert error.value == 'sqlite'

def test_get_config_value(config):
	assert config.get('database', 'driver') == 'sqlite'

def test_get_whole_section(config):
	assert config.get('database') == [('hash_imports', 'yes'), ('driver', 'sqlite')]

def test_contains_section(config):
	assert 'database' in config

def test_not_contains_section(config):
	assert 'xxxxxx' not in config

def test_contains_tuple(config):
	assert ('database', 'driver') in config

def test_not_contains_tuple(config):
	assert ('database', 'yyyyyyy') not in config

def test_get_config_multiple_files():
	config = rigor.config.RigorDefaultConfiguration(constants.kConfigFile, constants.kConfigFile2)
	assert config.getboolean('import', 'hash_imports') is False

def test_get_config_bad_section(config):
	with pytest.raises(rigor.config.NoSectionError) as error:
		config.get('xxxxxxxxx', 'yyyyyy')

def test_get_config_bad_value(config):
	with pytest.raises(rigor.config.NoValueError) as error:
		config.get('database', 'yyyyyy')
