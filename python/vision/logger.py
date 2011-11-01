import logging

_log = None

def getLogger(name, level=logging.DEBUG):
	global _log
	""" Returns a logger configured with Vision formatting """
	log = None
	if _log:
		log = _log
	else:
		log = logging.getLogger(name)
		_log = log
		console = logging.StreamHandler()
		console.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s'))
		log.addHandler(console)
	log.setLevel(level)
	return log
