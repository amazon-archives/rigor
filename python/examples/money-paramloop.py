"""
Used for testing money detector with ranges of parameters; stores JSON with parameters used and TSV:
image id\tdetected model\texpected model\telapsed time
"""

from rigor.config import config
from rigor.dbmapper import DatabaseMapper
from rigor.database import Database

import rigor.domain.money
import rigor.logger

from datetime import datetime
from functools import partial
import json

kDatabase = 'rigor'
kDomain = 'money'
kLimit = None

""" initial parameters overridden below """
parameters = {
	"grid_x_count": 4,
	"grid_y_count": 2,
	"group1_keypoint_count": 3,
	"group_count": 2,
	"image_keypoint_limit": 120,
	"knn_limit": 10,
	"match_params": [
		[ 0.6, 0.2, 0.8, 0.25, 0.2 ],
		[ 0.5, 0.18, 0.75, 0.25, 0.25 ]
	],
	"model_labels": [ 1, 1, 5, 5, 10, 10, 20, 20, 100, 100, 50, 50, 5, 5, 10, 10, 20, 20, 50, 50, 5, 5, 10, 10, 20, 20, 50, 50, 100, 100, 2, 2 ],
	"model_limit": 32,
	"model_names": [ "1a", "1b", "5a", "5b", "10a", "10b", "20a", "20b", "100a", "100b", "50a", "50b", "5c", "5d", "10c", "10d", "20c", "20d", "50c", "50d", "5e", "5f", "10e", "10f", "20e", "20f", "50e", "50f", "100c", "100d", "2a", "2b" ],
	"pass_limit": 2,
	"scale1": 0.2,
	"scale2": 0.35,
	"surf_params": [
		[ 500, 4, 2, 4, 4, 2 ],
		[ 600, 4, 2, 4, 4, 2 ]
	],
	"top_model_limit": 5
}

def get_parameters():
	for x in (0.6, 0.65):
		parameters["match_params"][0][1] = x
		for x in (0.8, 0.85):
			parameters["match_params"][0][2] = x
			for x in (0.5, 0.6):
				parameters["match_params"][1][0] = x
				for x in (0.18, 0.20, 0.22):
					parameters["scale1"] = x
					for x in (0.32, 0.35, 0.38):
						parameters["scale2"] = x
						for x in (400, 500, 600):
							parameters["surf_params"][0][1] = x
							for x in (2, 4):
								parameters["surf_params"][0][1] = x
								for x in (500, 600, 700):
									parameters["surf_params"][1][0] = x
									for x in (2, 4):
										parameters["surf_params"][1][1] = x
										yield parameters

def main():
	rigor.domain.money.init(parameters)
	logger = rigor.logger.getLogger(__file__)
	database_mapper = DatabaseMapper(Database.instance(kDatabase))
	logger.debug('Fetching image IDs from database')
	images = database_mapper.get_images_for_analysis(kDomain, kLimit, False)
	for parameter_set in get_parameters():
		timestamp = datetime.utcnow().strftime("{0}-%Y%m%d_%H%M%S%f".format(kDomain))
		with open("{0}.params".format(timestamp), "w") as parameter_file:
			json.dump(parameter_set, parameter_file)
			parameter_file.write("\n")

		with open("{0}.results".format(timestamp), "w") as result_file:
			image_config = partial(rigor.domain.money.run, parameters=parameter_set)
			logger.debug('Processing {0} images'.format(len(images)))
			for result in map(image_config, images):
				result_file.write("\t".join([str(x) for x in result]))
				result_file.write("\n")

if __name__ == '__main__':
	main()
