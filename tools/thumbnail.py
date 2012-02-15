#!/usr/bin/env python

"""
Generates thumbnails for images

Example crontab entry:

PYTHONPATH=/data/rigor/python
*/5 * * * * /usr/local/bin/python /data/rigor/tools/thumbnail.py
"""

import rigor.lockfile
import rigor.database
import rigor.dbmapper
import rigor.imageops

from rigor.config import config

import os
import subprocess
import sys
import errno


class Thumbnailer(object):
	""" Creates thumbnails """

	extensions = ('jpg', 'png')
	""" List of file extensions to thumbnail """

	def __init__(self):
		self._convert = os.path.abspath(config.get('thumbnail', 'convert_path'))
		self._lock_file = os.path.abspath(config.get('thumbnail', 'lock_file'))
		self._size = int(config.get('thumbnail', 'image_size'))
		self._database = rigor.database.Database()
		os.umask(002)

	def run(self):
		""" Acquires a lock and creates the thumbnails """
		with rigor.lockfile.LockFile(self._lock_file):
			with self._database.get_cursor(False) as cursor:
				cursor.execute("SELECT id, locator, format FROM image ORDER BY id;")
				images = cursor.fetch_all(rigor.dbmapper.image_mapper)
			for image in images:
				source_path = rigor.imageops.find(image)
				destination_path = rigor.imageops.find_thumbnail(image, self._size)
				if os.path.exists(destination_path):
					continue
				destination_dir = os.path.dirname(destination_path)
				try:
					os.makedirs(destination_dir)
				except OSError as err:
					if err.errno == errno.EEXIST:
						pass
					else:
						sys.stderr.write("Error creating {}\n".format(destination_dir))
						continue
				if subprocess.call((self._convert, source_path, '-resize', '{0}x{0}>'.format(self._size), destination_path)):
					sys.stderr.write("Error converting {}\n".format(source_path))
		return 0


if __name__ == '__main__':
	s = Thumbnailer()
	sys.exit(s.run())
