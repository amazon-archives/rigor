""" Logging functions """

import logging

__log__ = None

def get_logger(name, level=logging.DEBUG):
	""" Returns a logger configured with Rigor formatting """
	global __log__
	log = None
	if __log__:
		log = __log__
	else:
		log = logging.getLogger(name)
		__log__ = log
		console = logging.StreamHandler()
		console.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s'))
		log.addHandler(console)
	log.setLevel(level)
	return log
