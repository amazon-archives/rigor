#!/usr/bin/env python

"""
Synchronizes files from the import directory to the image directory.  Used to
allow users write access to the import directory, while retaining a read-only
image repository.

Example crontab entry:

PYTHONPATH=/data/rigor/python
*/5 * * * * /usr/local/bin/python /data/rigor/tools/sync.py
"""

from rigor.config import config

import os
import subprocess
import sys

class Synchronizer(object):
	""" Class containing methods for importing images into the Rigor framework """

	extensions = ('jpg', 'png')
	""" List of file extensions to synchronize """

	def __init__(self, move=True):
		self._source = os.path.abspath(config.get('import', 'upload_repository')) + os.sep
		self._destination = os.path.abspath(config.get('global', 'image_repository')) + os.sep
		self._move = move

		rsync = os.path.abspath(config.get('import', 'rsync_path'))

		args = [rsync, '-q', '-r', '-p', '--chmod=ugo+r,Dugo+x,ug+w', '-t', '-O']
		if move:
			args.append('--remove-source-files')
		args.append(self._source)
		args.append(self._destination)
		self._args = args
		os.umask(002)

	def run(self):
		""" Copies or moves all image files from source to destination directory """
		return subprocess.call(self._args)

if __name__ == '__main__':
	s = Synchronizer()
	sys.exit(s.run())
