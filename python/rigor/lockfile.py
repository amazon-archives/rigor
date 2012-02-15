""" File used to synchronize operations between processes """

import os

class LockFile(object):
	"""
	Use this to lock operations that need to occur only once, even if several
	processes try to run the operation.  It works by getting an exclusive lock on
	the listed file.  It will fail with an exception if the lock already is held
	by some other process.

	Usage:
		>>> with LockFile('/tmp/rigor-foo.lock') as lock:
		...		# do critical stuff...
		...		pass
	"""

	def __init__(self, path):
		self._path = path
		self._lock = None

	def acquire(self):
		self._lock = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_RDWR)

	def release(self):
		if self._lock:
			os.close(self._lock)
			os.unlink(self._path)

	def __enter__(self):
		if not self._lock:
			self.acquire()
		return self

	def __exit__(self, type, value, traceback):
		self.release()
