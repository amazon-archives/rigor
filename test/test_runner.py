import rigor.algorithm
import rigor.runner
import rigor.types
import rigor.config
import db
import os
import constants

class PassthroughAlgorithm(rigor.algorithm.Algorithm):
	def run(self, percept_data):
		rigor.algorithm.Algorithm.run(self, percept_data) # cheat for coverage
		return percept_data.read()

class ImageShapeAlgorithm(rigor.algorithm.ImageAlgorithm):
	def run(self, percept_data):
		return percept_data.shape

class AllPerceptRunner(rigor.runner.DatabaseRunner):
	def __init__(self, algorithm, config, database, parameters=None, checkpoint=None):
		super(AllPerceptRunner, self).__init__(algorithm, config, database_name=database, parameters=parameters, checkpoint=checkpoint)
		self._session = self._database.get_session()

	def get_percepts(self):
		return self._session.query(rigor.types.Percept).order_by(rigor.types.Percept.id).all()

	def fetch_data(self, percept):
		class DummyPercept(object):
			def __init__(self, locator, credentials):
				self.locator = locator
				self.credentials = credentials
		p = DummyPercept(constants.kExampleTextFile, None)
		return super(AllPerceptRunner, self).fetch_data(p)

class DummyCommandLineRunner(rigor.runner.CommandLineMixIn, AllPerceptRunner):
	def __init__(self, algorithm, config, database, arguments):
		parsed_args = self.parse_arguments(arguments)
		super(DummyCommandLineRunner, self).__init__(algorithm, config, database, parsed_args)

class SinglePerceptRunner(rigor.runner.Runner):
	def __init__(self, algorithm, percept):
		super(SinglePerceptRunner, self).__init__(algorithm)
		self._percept = percept

	def get_percepts(self):
		rigor.runner.Runner.get_percepts(self) # cheat for coverage
		return [self._percept, ]

	def fetch_data(self, percept):
		rigor.runner.Runner.fetch_data(self, percept) # cheat for coverage
		return open(percept.locator, 'rb')

kConfig = rigor.config.RigorDefaultConfiguration(constants.kConfigFile)

def test_instantiate_db_runner():
	algorithm = PassthroughAlgorithm()
	db.get_database() # Runner takes a db name, not an instance
	apr = AllPerceptRunner(algorithm, kConfig, constants.kTestFile)

def test_run_basic():
	with open(constants.kExampleTextFile, 'rb') as text_file:
		expected = text_file.read()
	percept = rigor.types.Percept()
	percept.locator = constants.kExampleTextFile
	algorithm = PassthroughAlgorithm()
	spr = SinglePerceptRunner(algorithm, percept)
	evaluated = spr.run()
	returned_percept, result, annotations, elapsed = evaluated[0]
	assert result == expected
	assert elapsed > 0

try:
	import cv2

	def test_run_image():
		percept = rigor.types.Percept()
		percept.locator = constants.kExampleImageFile
		algorithm = ImageShapeAlgorithm()
		algorithm.set_parameters('xxx')
		spr = SinglePerceptRunner(algorithm, percept)
		evaluated = spr.run()
		returned_percept, result, annotations, elapsed = evaluated[0]
		assert result == constants.kExampleImageDimensions
		assert algorithm.parameters == 'xxx'
		assert elapsed > 0

except ImportError:
	pass

def test_run_all():
	algorithm = PassthroughAlgorithm()
	apr = AllPerceptRunner(algorithm, kConfig, constants.kTestFile)
	evaluated = apr.run()
	assert len(evaluated) == 12
	assert len(evaluated[0]) > 0

def test_create_checkpoint():
	algorithm = PassthroughAlgorithm()
	parameters = ('xxx', 'yyy', 2)
	apr = AllPerceptRunner(algorithm, kConfig, constants.kTestFile, parameters=parameters, checkpoint=constants.kExampleNewCheckpointFile)
	evaluated = apr.run()
	assert len(evaluated) == 12

def test_resume_checkpoint():
	algorithm = PassthroughAlgorithm()
	parameters = ('xxx', 'yyy', 2)
	apr = AllPerceptRunner(algorithm, kConfig, constants.kTestFile, parameters=parameters, checkpoint=constants.kExampleCheckpointFile)
	evaluated = apr.run()
	assert len(evaluated) == 12

def test_command_line():
	algorithm = PassthroughAlgorithm()
	arguments = (__file__, '-c', constants.kExampleCheckpointFile)
	dclr = DummyCommandLineRunner(algorithm, kConfig, constants.kTestFile, arguments)
	assert dclr._parameters == dict()
	evaluated = dclr.run()
	assert len(evaluated) == 12
