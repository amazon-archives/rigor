import rigor.logger

def test_logger_once():
	logger = rigor.logger.get_logger(__file__)
	logger.debug('Logger call A')

def test_logger_twice():
	logger = rigor.logger.get_logger(__file__)
	logger.debug('Logger call B')
	logger = rigor.logger.get_logger(__file__)
	logger.debug('Logger call C')
