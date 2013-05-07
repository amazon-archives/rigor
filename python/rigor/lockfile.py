""" File used to synchronize operations between processes """

import os

class LockFile(object):
	"""
	Use this to lock operations that need to occur only once, even if several
	processes try to run the operation.  It works by getting an exclusive lock on
	the listed file.  It will fail with an exception if the lock already is held
	by some other process.  Note that the lock is reentrant for any code sharing
	the same instance of this class.

	Usage:
		>>> with LockFile('/tmp/rigor-foo.lock') as lock:
		...		# do critical stuff...
		...		pass
	"""

	def __init__(self, path):
		self._path = path
		self._lock = None

	def acquire(self):
		"""
		Acquires a reentrant lock.  If the lock already exists in this method, it
		will simply return; otherwise, it will acquire the lock.  It will throw an
		exception if the lock cannot be acquired.
		"""
		if not self._lock:
			self._lock = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_RDWR)

	def release(self):
		"""
		Releases the lock and removes the file from disk.
		"""
		if self._lock:
			os.close(self._lock)
			os.unlink(self._path)

	def __enter__(self):
		self.acquire()
		return self

	def __exit__(self, _exc_type, _exc_value, _exc_traceback):
		self.release()
