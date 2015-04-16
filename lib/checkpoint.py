""" Saved progress for Rigor, allowing users to resume long-running runs that fail part way through """

import rigor.logger
import tempfile
import time
import cPickle as pickle
import os

kPickleProtocol = pickle.HIGHEST_PROTOCOL

class Checkpoint(object):
	""" Saved checkpoint results, loaded from a file """

	def __init__(self, timestamp, parameters, seen, results):
		"""
		:param timestamp: when the checkpoint file was first created
		:param dict parameters: parameters used in the original run
		:param set(int) seen: a set of IDs that have been checkpointed already, to make it easy to skip duplicate evaluations
		:param results: the saved results
		"""
		self.timestamp = timestamp
		self.parameters = parameters
		self.seen = seen
		self.results = results

class NullCheckpointer(object):
	"""
	Does nothing. Used in place of actual checkpointer to make code simpler in :py:class:`~rigor.Runner`.
	"""
	def log(self, id, entry, flush=True):
		pass

	def __enter__(self):
		return self

	def __exit__(self, exc_type, value, traceback):
		pass

class Checkpointer(object):
	"""
	Saves progress of algorithm evaluations in a file, to be loaded later
	if there is an error and the evaluation is interrupted
	"""

	def __init__(self, parameters, checkpoint_file=None, delete_on_success=True):
		"""
		:param parameters: parameters that were used to generate checkpointed results
		:param file checkpoint_file: open file to use for checkpointing, or :py:class:`None` to create a new one
		:param delete_on_success: whether to delete the checkpoint file when closed
		"""
		self._logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self._parameters = parameters
		if not checkpoint_file:
			self._file = tempfile.NamedTemporaryFile('wb', prefix='rigor-checkpoint-', delete=False)
			self.filename = self._file.name
		else:
			self._file = checkpoint_file
			self.filename = checkpoint_file.name
		self._delete = delete_on_success
		self._write_header()
		self._logger.info("Checkpoint filename is {}".format(self.filename))

	def _write_header(self):
		""" Writes an identifying header to the checkpoint file """
		pickle.dump(time.time(), self._file, kPickleProtocol)
		pickle.dump(self._parameters, self._file, kPickleProtocol)

	def log(self, id, entry, flush=True):
		"""
		Logs a checkpoint entry to the file

		:param id: The percept ID
		:param entry: structured data returned from Algorithm.apply()
		:param flush: whether to flush file output with each log entry (safer, but slower if processing each percept is very quick)
		"""
		pickle.dump((id, entry), self._file, kPickleProtocol)
		if flush:
			self._file.flush()

	def close(self, success):
		"""
		Closes the checkpoint file.

		:param success: whether operation finished successfully
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

		:param checkpoint_file: file open in :py:const:`rb` mode containing a checkpoint
		"""
		timestamp = pickle.load(checkpoint_file)
		parameters = pickle.load(checkpoint_file)
		return timestamp, parameters

	@classmethod
	def resume(cls, old_file, new_file=None, delete_on_success=True):
		"""
		Resumes from an existing checkpoint file.

		:param file old_file: existing open checkpoint file to resume from
		:param file new_file: open new checkpoint file (must be different from the old file)
		:param delete_on_success: whether to delete the new checkpoint file when closed, if successful

		:return: (Checkpointer object, Checkpoint object)
		"""
		timestamp, parameters = cls.read_header(old_file)
		checkpointer = cls(parameters, new_file, delete_on_success)
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
		return checkpointer, Checkpoint(timestamp, parameters, seen, entries)
