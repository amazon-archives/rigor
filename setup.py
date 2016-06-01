from setuptools import setup
from setuptools.command.test import test as TestCommand
from glob import glob
import os.path
import sys

class PyTest(TestCommand):
	user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

	def initialize_options(self):
		TestCommand.initialize_options(self)
		self.pytest_args = list()

	def finalize_options(self):
		TestCommand.finalize_options(self)
		self.test_args = list()
		self.test_suite = True

	def run_tests(self):
		import pytest
		errno = pytest.main(self.pytest_args)
		sys.exit(errno)

scripts = glob(os.path.join('tools', '*.py'))
scripts.extend(glob(os.path.join('bin', '*.py')))

setup(
		name = 'Rigor',
		version = '2.1.0',
		description = 'The Rigor testing framework',
		long_description = 'Rigor is a framework for managing labeled data, and for testing algorithms against that data in a systematic fashion.',
		maintainer = 'David Wallace',
		maintainer_email = 'dtw@a9.com',
		url = 'https://github.com/blindsightcorp/rigor',
		license = 'BSD License',
		install_requires = ['SQLAlchemy >= 0.7.6', 'alembic >= 0.7.3'],
		tests_require = ['pytest >= 2.5.2', 'moto >= 0.4'],
		cmdclass = {'test': PyTest, },
		packages = ('rigor', ),
		package_dir = { 'rigor': 'lib', },
		scripts=scripts,
		classifiers = [
			'Development Status :: 5 - Production/Stable',
			'Intended Audience :: Science/Research',
			'License :: OSI Approved :: BSD License',
			'Natural Language :: English',
			'Programming Language :: Python :: 2',
			'Programming Language :: Python :: 3',
			'Topic :: Scientific/Engineering :: Artificial Intelligence',
			'Topic :: Utilities',
		],
)
