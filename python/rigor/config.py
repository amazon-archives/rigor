""" Configuration """

import os
from ConfigParser import RawConfigParser
import multiprocessing

kConfigurationPath = os.path.join(os.environ['HOME'], '.rigor.ini')

_defaults = dict(
		max_workers = multiprocessing.cpu_count(),
		copy_local = 'yes',
		database = 'rigor',
		ssl = 'yes',
		min_database_connections = 0,
		max_database_connections = 10,
		metadata_file = 'metadata.json',
		timestamp_format = '%Y-%m-%dT%H:%M:%SZ'
	)
config = RawConfigParser(_defaults)
config.read(kConfigurationPath)
