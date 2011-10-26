"""
This has workers executing incoming tasks as soon as they can.  If
no workers are available (and none can be launched), the task will be
queued and processed when possible.
"""
import vision.logger
from vision.exceptions import ThreadingError

import threading
import inspect
import ctypes

from threading import Thread
from Queue import Queue
from Queue import Empty

_QUIT = None

class ThreadPool(object):
	"""
	Handles incoming tasks, farming them out to workers.  Note that
	it may take up to the call_queue_poll_timeout interval for all of the
	workers to shut down, so keep it reasonably low
	"""
	def __init__(self, max_workers=10, call_queue_poll_timeout=10):
		self._logger = vision.logger.getLogger(".".join((__name__, self.__class__.__name__)))
		self._max_workers = max_workers
		self._call_queue_poll_timeout = call_queue_poll_timeout
		self._call_queue = Queue()
		self._workers = list()
		self._active = True
		self._logger.debug("ThreadPool initialized with {0} workers".format(max_workers))

	def call_in_thread(self, target, args=None, kwargs=None):
		""" Puts the task onto the work queue to be processed when next possible """
		if args is None:
			args = list()
		if kwargs is None:
			kwargs = dict()

		if self._active:
			self._call_queue.put((target, args, kwargs))
			self._launch_workers()
		else:
			raise ThreadingError("ThreadPool is shutting down")

	def shutdown(self):
		""" Shuts down worker threads """
		self._active = False
		for thread in self._workers:
			if thread != threading.current_thread():
				thread.join()

	def start(self):
		"""
		Allows more tasks to be launched.  This only needs to be called if
		shutdown() has already been called.
		"""
		self._active = True

	def _launch_workers(self):
		if len(self._workers) < self._call_queue.qsize() and len(self._workers) < self._max_workers:
			worker = Thread(target=self._process_queue)
			worker.name = 'worker' + worker.name
			worker.daemon = True
			self._workers.append(worker)
			worker.start()
			self._logger.debug("Launched {0}".format(worker.name))

	def _process_queue(self):
		while self._active:
			try:
				task = self._call_queue.get(True, self._call_queue_poll_timeout)
				target, args, kwargs = task
				target(*args, **kwargs)
			except Empty:
				pass
		self._logger.debug("{0} exiting".format(threading.current_thread().name))

class KillableThread(Thread):
	""" A thread that can be killed from another thread """

	def _get_thread_id(self):
		""" Gets the thread ID """
		if not self.is_alive():
			raise threading.ThreadError("the thread is not active")

		# do we have it cached?
		if hasattr(self, "_thread_id"):
			return getattr(self, "_thread_id")

		# no, look for it in the _active dict
		for tid, tobj in threading._active.items():
			if tobj is self:
				self._thread_id = tid
				return tid

		raise ThreadingError("could not determine the thread's id")

	def _async_raise(self, exctype):
		""" Raises the exception, performs cleanup if needed """
		if not inspect.isclass(exctype):
			raise TypeError("Only types can be raised (not instances)")
		tid = self._get_thread_id()
		res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
		if res == 0:
			raise ValueError("invalid thread id")
		elif res != 1:
			# if it returns a number greater than one, you're in trouble,
			# and you should call it again with exc=NULL to revert the effect
			ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
			raise SystemError("PyThreadState_SetAsyncExc failed")

	def raise_exception(self, exctype):
		""" raises the given exception type in the context of this thread """
		self._async_raise(exctype)

	def terminate(self):
		"""
		raises SystemExit in the context of the given thread, which should
		cause the thread to exit silently (unless caught)
		"""
		self.raise_exception(SystemExit)
