import logging

def getLogger(name, level=logging.DEBUG):
	""" Returns a logger configured with Vision formatting """
	log = logging.getLogger(name)
	log.setLevel(level)
	console = logging.StreamHandler()
	console.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s'))
	log.addHandler(console)
	return log
