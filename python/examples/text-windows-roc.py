"""
Runs the text detector algorithm, getting low-level texture-detection returns; passes on
list of detected and undetected windows that can be used with the ground truth ROIs to
generate ROC curves.
"""

import rigor.runner
from rigor.database import Database
from rigor.dbmapper import DatabaseMapper

import argparse

from shapely.geometry import Polygon

parameters = {
	"pyramid_step": 2,
	"pyramid_substep": 1.25,
	"pyramid_num_substeps": 5,
	"pyramid_min_width": 20,
	"pyramid_min_height": 10,
	"pyramid_window_width": 20,
	"pyramid_window_height": 10,
	"cluster_min_area": 600,
	"cluster_min_weight": 1.0,
	"minimum_percent_overlap": 0.2
}

def main():
	results = open('results.txt','w')
	parser = argparse.ArgumentParser(description='Runs text detector on relevant images at window level')
	parser.add_argument('classifier_file', help='Path to classifier CLF')
	parser.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	args = parser.parse_args()
	parameters["classifier_file"] = args.classifier_file
	parameters["evaluate_windows"] = True
	i = rigor.runner.Runner('text', parameters, limit=args.limit, random=args.random)
	database_mapper = DatabaseMapper(Database())
	results.write("threshold\timageid\texpected\tdetected\n")
	for cascade_threshold in (.5,):
		parameters['cascade_threshold'] = cascade_threshold
		for result in i.run():
			image_id = result[0]
			detected = result[1]
			undetected = result[2]
			expected_blob = Polygon()
			for expected in result[3]:
				expected_blob = expected_blob.union(Polygon(expected))
			for dbox in detected:
				box = Polygon(dbox)
				intersection = expected_blob.intersection(box)
				if intersection and (intersection.area / box.area) > parameters["minimum_percent_overlap"]:
					results.write("{}\t{}\t1\t1\t\n".format(cascade_threshold,image_id))
				else:
					results.write("{}\t{}\t1\t0\t\n".format(cascade_threshold,image_id))
			for dbox in undetected:
				box = Polygon(dbox)
				intersection = expected_blob.intersection(box)
				if intersection and (intersection.area / box.area) > parameters["minimum_percent_overlap"]:
					results.write("{}\t{}\t0\t1\t\n".format(cascade_threshold,image_id))
				else:
					results.write("{}\t{}\t0\t0\t\n".format(cascade_threshold,image_id))

if __name__ == '__main__':
	main()
