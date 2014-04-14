#!/usr/bin/env python

from distutils.core import setup
import glob
import os

scripts=glob.glob(os.path.join('tools', '*.py'))
scripts.append('python/import.py')

sql=glob.glob(os.path.join('sql', '*.sql'))

setup(name='Rigor',
	version='1.0.1',
	description='The Rigor testing framework',
	author='Kevin Rauwolf',
	author_email='kevin@blindsight.com',
	url='https://github.com/blindsightcorp/rigor',
	package_dir = {'': 'python'},
	packages=['rigor',],
	scripts=scripts,
	data_files=[
		('sql', sql),
	]
)
