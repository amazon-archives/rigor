import rigor.algorithm
import rigor.runner
import rigor.types
import rigor.config

class PassthroughAlgorithm(rigor.algorithm.Algorithm):
	def run(self, percept_data):
		return percept_data.read()

class AllPerceptRunner(rigor.runner.DatabaseRunner):
	def __init__(self, algorithm, config, database):
		super(AllPerceptRunner, self).__init__(algorithm, config, database_name=database)
		self._session = self._database.get_session()

	def get_percepts(self):
		return self._session.query(rigor.types.Percept).order_by(rigor.types.Percept.id).all()

	def evaluate(self, results):
		print('Percept\tExpected\tActual')
		for percept, result, annotations, elapsed in results:
			print('\t'.join((str(percept.id), annotations[0].model, result)))

config = rigor.config.RigorDefaultConfiguration()
algorithm = PassthroughAlgorithm()
runner = AllPerceptRunner(algorithm, config, 'tutorial.db')
runner.run()
