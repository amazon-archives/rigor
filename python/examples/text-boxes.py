"""
Runs the text detector algorithm, getting top-level ROI returns, and draws
those ROIs in addition to the ground truthon a copy of the image
"""

import rigor.runner
import rigor.imageops
from rigor.database import Database
from rigor.dbmapper import DatabaseMapper

import argparse
import cv2

parameters = {
	"pyramid_step": 2,
	"pyramid_substep": 1.25,
	"pyramid_num_substeps": 5,
	"pyramid_min_width": 20,
	"pyramid_min_height": 10,
	"pyramid_window_width": 20,
	"pyramid_window_height": 10,
	"cluster_min_area": 600,
	"cluster_min_weight": 1.0
}

def main():
	parser = argparse.ArgumentParser(description='Runs text detector on relevant images')
	parser.add_argument('classifier_file', help='Path to classifier CLF')
	parser.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	parser.add_argument('database', help='Database to use')
	args = parser.parse_args()
	parameters["classifier_file"] = args.classifier_file
	i = rigor.runner.Runner('text', parameters, limit=args.limit, random=args.random)
	database_mapper = DatabaseMapper(Database(args.database))
	for result in i.run():
		detected = result[1]
		expected = result[2]
		image = database_mapper.get_image_by_id(result[0])
		cv_image = rigor.imageops.fetch(image)
		cv2.polylines(cv_image, expected, True, cv2.RGB(0, 255, 0))
		cv2.polylines(cv_image, detected, True, cv2.RGB(255, 255, 0))
		cv2.imwrite(".".join((str(image["id"]), image["format"])), cv_image)

if __name__ == '__main__':
	main()
