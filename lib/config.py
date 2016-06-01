""" Handles configuration needed for Rigor """

from abc import ABCMeta, abstractmethod
import ConfigParser
import os
import rigor.logger

#: Default filename for a parsed .ini file

if 'HOME' in os.environ:
	kDefaultConfigurationPath = os.path.join(os.environ['HOME'], '.rigor.ini')
else:
	kDefaultConfigurationPath = os.path.join(os.getcwd(), '.rigor.ini')

class ConfigurationError(StandardError):
	""" Base class for configuration-related errors """
	pass

class NoSectionError(ConfigurationError):
	""" Exception raised when the specified section is not found """
	pass

class NoValueError(ConfigurationError):
	""" Exception raised when a value is not found for a given key """
	pass

class RigorConfiguration(object):
	"""
	Describes a protocol for accessing configuration values.

	Configuration is divided into sections of key-value pairs. There is also a set of defaults, which apply to all sections.
	"""
	__metaclass__ = ABCMeta

	# Global default values
	kDefaults = dict(
			hash_imports = 'yes',
	)

	# Used by getboolean to transform raw values to booleans
	_boolean_transformer = {
		'1': True,
		'yes': True,
		'true': True,
		'on': True,
		'0': False,
		'no': False,
		'false': False,
		'off': False,
	}

	def __init__(self):
		self._logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self._logger.debug("Using {}".format(self.__class__.__name__))

	@abstractmethod
	def get(self, section, key=None):
		"""
		Gets a single configuration value unchanged

		:param str section: Section name
		:param str key: Configuration key name. If no key is given, a list of (key, value) pairs for each item in the section will be returned
		:return: the value for the given key, or all key-value pairs in the section if no key
		:raises rigor.config.NoSectionError: if the specified section does not exist
		:raises rigor.config.NoValueError: if the specified key does not exist in that section
		"""

	def getboolean(self, section, key):
		"""
		Gets a single configuration value, coerced into a boolean. :py:const:`"1"`, :py:const:`"yes"`, :py:const:`"true"`, and :py:const:`"on"` are considered :py:const:`True`, and :py:const:`"0"`, :py:const:`"no"`, :py:const:`"false"`, and :py:const:`"off"` are considered :py:const:`False`.

		:param str section: Section name
		:param str key: Configuration key name
		:return: the value for the given key
		:raises rigor.config.NoSectionError: if the specified section does not exist
		:raises rigor.config.NoValueError: if the specified key does not exist in that section
		:raises ValueError: if the value cannot be coerced to a boolean
		"""
		value = self.get(section, key)
		if value is True or value is False:
			return value
		lower = value.lower()
		if lower not in self._boolean_transformer:
			raise ValueError(value)
		return self._boolean_transformer[lower]

	def __contains__(self, key):
		"""
		If the key is a single string, then this will check whether a section with that name exists in the configuration. If it is a tuple, then it will check both section and key. The default implementation always returns :py:const:`True`.
		"""
		return True

class RigorIniConfiguration(RigorConfiguration):
	"""
	Configuration values are read from a :file:`.rigor.ini` file

	:param str paths: Paths to configuration files, as strings
	"""

	def __init__(self, *paths):
		super(RigorIniConfiguration, self).__init__()
		if not paths:
			paths = (kDefaultConfigurationPath, )
		self._parser = ConfigParser.RawConfigParser(self.kDefaults)
		self._logger.debug("Reading configuration from {}".format(paths))
		self._parser.read(paths)

	def get(self, section, key=None):
		""" See :py:meth:`RigorConfiguration.get` """
		try:
			if key is None:
				return self._parser.items(section)
			return self._parser.get(section, key)
		except ConfigParser.NoSectionError as err:
			raise NoSectionError(err)
		except ConfigParser.NoOptionError as err:
			raise NoValueError(err)

	def getboolean(self, section, key):
		""" See :py:meth: `RigorConfiguration.getBoolean` """
		return super(RigorIniConfiguration, self).getboolean(section, key)

	def __contains__(self, key):
		""" See :py:meth:`RigorConfiguration.__contains__` """
		if hasattr(key, 'strip'):
			# It's string-like
			return self._parser.has_section(key)
		section, key = key
		return self._parser.has_option(section, key)

RigorDefaultConfiguration = RigorIniConfiguration
