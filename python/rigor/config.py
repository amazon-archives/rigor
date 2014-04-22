""" Configuration """

import os
from ConfigParser import RawConfigParser
import multiprocessing

kConfigurationPath = os.path.join(os.environ['HOME'], '.rigor.ini')

__defaults__ = dict(
		max_workers = multiprocessing.cpu_count(),
		copy_local = 'yes',
		ssl = 'yes',
		min_database_connections = 0,
		max_database_connections = 10,
		adaptor = 'psycopg2',
		metadata_file = 'metadata.json',
		timestamp_format = '%Y-%m-%dT%H:%M:%SZ'
	)
config = RawConfigParser(__defaults__) # pylint: disable=C0103
config.read(kConfigurationPath)
