"""
Saved progress for Rigor, allowing users to resume long-running runs that
fail part way through
"""

import rigor.logger
import tempfile
import argparse
import time
import json
import cPickle as pickle
import os

kPickleProtocol = pickle.HIGHEST_PROTOCOL

class Checkpoint(object):
	""" Saved checkpoint results, loaded from a file """

	def __init__(self, timestamp, arguments, seen, results):
		"""
		timestamp - when the checkpoint file was first created
		arguments - command line arguments used in the original run
		seen - a set of IDs that have been checkpointed already, to make it easy to
		skip duplicate evaluations
		results - the saved results
		"""
		self.timestamp = timestamp
		self.arguments = arguments
		self.seen = seen
		self.results = results

class Checkpointer(object):
	"""
	Saves progress of algorithm evaluations in a file, to be loaded later
	if there is an error and the evaluation is interrupted
	"""

	def __init__(self, arguments, filename=None, delete_on_success=True):
		"""
		arguments - arguments that were used to generate checkpointed results
		filename - checkpoint filename
		delete_on_success - whether to delete the checkpoint file when closed
		"""
		self._logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self._arguments = vars(arguments)
		if not filename:
			self._file = tempfile.NamedTemporaryFile('wb', prefix='rigor-checkpoint-', delete=False)
			self.filename = self._file.name
		else:
			self._file = open(filename, 'wb')
			self.filename = filename
		self._delete = delete_on_success
		self._write_header()
		self._logger.info("Checkpoint filename is {}".format(self.filename))

	def _write_header(self):
		""" Writes an identifying header to the checkpoint file """
		pickle.dump(time.time(), self._file, kPickleProtocol)
		pickle.dump(self._arguments, self._file, kPickleProtocol)

	def log(self, id, entry, flush=True):
		"""
		Logs a checkpoint entry to the file

		id - The image ID
		entry - structured data returned from Algorithm.apply()
		flush - whether to flush file output with each log entry (safer, but slower
		if processing each image is very quick)
		"""
		pickle.dump((id, entry), self._file, kPickleProtocol)
		if flush:
			self._file.flush()

	def close(self, success):
		"""
		Closes the checkpoint file.
		
		success - whether operation finished successfully
		"""
		self._file.close()
		if self._delete and success:
			os.remove(self.filename)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, value, traceback):
		self.close(exc_type is None)

	@classmethod
	def read_header(cls, checkpoint_file):
		"""
		Loads just the header portion of a checkpoint file.

		checkpoint_file - file open in 'rb' mode containing a checkpoint
		"""
		timestamp = pickle.load(checkpoint_file)
		# It seems argparse.Namespace pickles (or at least unpickles) as a dict
		arguments_dict = pickle.load(checkpoint_file)
		arguments = argparse.Namespace()
		vars(arguments).update(arguments_dict)
		return timestamp, arguments

	@classmethod
	def resume(cls, old_filename, new_filename=None, delete_on_success=True):
		"""
		Resumes from an existing checkpoint file.

		old_filename - existing checkpoint filename to resume from
		new_filename - name of new checkpoint filename (must be different from the
		old filename)
		delete_on_success - whether to delete the new checkpoint file when
		closed

		returns a tuple of (Checkpointer object, Checkpoint object)
		"""
		with open(old_filename, 'rb') as old_file:
			timestamp, arguments = cls.read_header(old_file)
			checkpointer = cls(arguments, new_filename, delete_on_success)
			entries = list()
			seen = set()
			while True:
				try:
					id, entry = pickle.load(old_file)
					seen.add(id)
					entries.append(entry)
					checkpointer.log(id, entry, flush=False)
				except EOFError:
					break
			return checkpointer, Checkpoint(timestamp, arguments, seen, entries)
