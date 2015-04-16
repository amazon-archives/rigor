import pytest
import shutil
import os.path
from rigor.config import RigorDefaultConfiguration
from rigor.database import Database
from rigor.types import Percept
import constants

kConfig = RigorDefaultConfiguration(constants.kConfigFile)

def get_database():
	shutil.copyfile(constants.kFixtureFile, constants.kTestFile)
	database = Database(constants.kTestFile, kConfig)
	return database
