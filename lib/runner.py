""" Runs an algorithm across a set of percepts.  Result is a report containing percept ID, detected model, expected model, and elapsed time """

import rigor.logger
from rigor.database import Database
from rigor.perceptops import PerceptOps
from rigor.checkpoint import Checkpointer, NullCheckpointer

import abc
import argparse
import os.path

kArgumentsKey = 'arguments'

class Runner(object):
	"""
	The base class for Runner objects, which fetch a set of percepts and apply
	the :py:class:`~rigor.algorithm.Algorithm` instance to each

	:param algorithm: algorithm to run against each percept
	:type algorithm: :py:class:`~rigor.algorithm.Algorithm`
	:param dict parameters: settings for the Runner
	:param str checkpoint: can be path of an existing :py:class:`~rigor.checkpoint.Checkpoint` file to resume from, the path to a new one, or :py:const:`None` to skip checkpointing
	"""
	__metaclass__ = abc.ABCMeta

	def __init__(self, algorithm, parameters=None, checkpoint=None):
		self._logger = rigor.logger.get_logger('.'.join((__name__, self.__class__.__name__)))
		self._algorithm = algorithm
		if parameters is None:
			parameters = dict()
		self._parameters = parameters
		self._checkpoint_filename = checkpoint

	@abc.abstractmethod
	def get_percepts(self):
		"""
		Fetches percepts to be run against the :py:class:`~rigor.algorithm.Algorithm`, with annotations included to check against the results. It is called by the :py:meth:`run` method, and must be overridden.
		"""
		pass

	@abc.abstractmethod
	def fetch_data(self, percept):
		""" Fetches percept data and returns it as a contextmanager """
		pass

	def run(self):
		""" This is the method called to run the algorithm. """
		percepts = self.get_percepts()
		checkpoint_status = ''
		results = list()
		checkpointer = NullCheckpointer()
		if self._checkpoint_filename:
			if os.path.exists(self._checkpoint_filename):
				with open(self._checkpoint_filename, 'rb') as old_checkpoint_file:
					checkpointer, checkpoint = Checkpointer.resume(old_checkpoint_file)
				results = checkpoint.results
				seen = checkpoint.seen
				percepts = [percept for percept in percepts if percept.id not in seen]
				checkpoint_status = ' (skipping {0} checkpointed)'.format(len(seen))
			else:
				checkpoint_file = open(self._checkpoint_filename, 'wb')
				checkpointer = Checkpointer(self._parameters, checkpoint_file)
		self._logger.debug('Processing {0} percepts{1}'.format(len(percepts), checkpoint_status))
		with checkpointer:
			for percept in percepts:
				percept = self._algorithm.prefetch(percept)
				with self.fetch_data(percept) as percept_data:
					result = self._algorithm.apply(percept, percept_data)
				checkpointer.log(percept.id, result)
				results.append(result)
		return self.evaluate(results)

	def evaluate(self, results):
		"""
		This takes the final output of all applications of the algorithm and
		formats it into a useful report.  It can optionally return results (that's
		up to the implementer), but its main function should be to create reports
		and format output.  The default implementation simply prints the results to
		stdout
		"""
		print(results)
		return results # why not?

class CommandLineMixIn(object):
	"""
	Provides helpers for parsing command-line arguments
	"""

	def parse_arguments(self, arguments):
		"""
		Parses command-line arguments, and returns the result
		"""
		checkpoint_parser = argparse.ArgumentParser(add_help=False)
		checkpoint_parser.add_argument('-c', '--checkpoint', type=argparse.FileType('rb'), required=False, help='Resume from checkpoint file. If you specify this, all other options will be ignored.')
		checkpoint_args, remaining = checkpoint_parser.parse_known_args(arguments)
		if checkpoint_args.checkpoint:
			_, arguments = Checkpointer.read_header(checkpoint_args.checkpoint)
			self._checkpoint_filename = checkpoint_args.checkpoint
			return arguments
		parser = argparse.ArgumentParser(description='Runs algorithm on relevant percepts', conflict_handler='resolve', usage='%(prog)s {-c | [options]}', parents=[checkpoint_parser, ])
		self.add_arguments(parser)
		return parser.parse_args(remaining)

	def add_arguments(self, parser):
		"""
		This method can be overridden to add additional arguments or otherwise
		modify the argument parser before it runs :py:meth:`~argparse.ArgumentParser.parse_args`.

		:param parser: The argument parser
		:type parser: :py:class:`argparse.ArgumentParser`
		"""
		pass

class DatabaseRunner(Runner):
	"""
	Runner class that uses the database to discover percepts for evaluation

	:param algorithm: algorithm to run against each percept
	:type algorithm: :py:class:`~rigor.algorithm.Algorithm`
	:param config: configuration data
	:type config: :py:class:`~rigor.config.RigorConfiguration`
	:param str database_name: name of the database to use
	:param dict parameters: settings for the Runner
	:param file checkpoint: open :py:class:`~rigor.checkpoint.Checkpoint` file to resume from
	"""

	def __init__(self, algorithm, config, database_name, parameters=None, checkpoint=None):
		Runner.__init__(self, algorithm, parameters, checkpoint)
		self._config = config
		self._database = Database(database_name, config)
		self._perceptops = PerceptOps(config)

	def fetch_data(self, percept):
		"""
		Gets percept data from the repository

		:param percept: The percept corresponding to data to fetch
		:return: Percept data encapsulated in a :py:func:`~contextlib.contextmanager`
		"""
		return self._perceptops.fetch(percept)
