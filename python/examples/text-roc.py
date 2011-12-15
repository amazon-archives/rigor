"""
Runs the text detector on images for a range of cascade_threshold values, stores FP, TP, FN in results.txt; feed this to text-roc-curve.php to see stats that can be plugged into a graph for an ROC curve.
"""

import rigor.runner
import rigor.imageops
from rigor.database import Database
from rigor.dbmapper import DatabaseMapper

import argparse
import Image, ImageDraw

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
	"cluster_min_weight": 1.0
}

def main():
	results = open('results.txt','w')
	parser = argparse.ArgumentParser(description='Runs text detector on relevant images')
	parser.add_argument('classifier_file', help='Path to classifier CLF')
	parser.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	args = parser.parse_args()
	parameters["classifier_file"] = args.classifier_file
	#database_mapper = DatabaseMapper(Database()) # unused!?
	results.write("threshold\texpected\tdetected\texpected_box\tdetected_box\n")
	#for cascade_threshold in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
	for cascade_threshold in (.5,.6):
		parameters['cascade_threshold'] = cascade_threshold
		i = rigor.runner.Runner('text', parameters, args.limit, args.random)
		for result in i.run():
			detected = result[1]
			expected = result[2]
			for ebox in expected:
				expected_box = Polygon(ebox)
				closest_detected = None
				closest_intersection = None
				closest_distance = None
				#find the closest/most overlapping from detected
				for dbox in detected:
					detected_box = Polygon(dbox)
					intersection = detected_box.intersection(expected_box);
					if intersection:
						distance = detected_box.centroid.distance(expected_box.centroid)
						if distance < closest_distance or not closest_distance:
							closest_detected = dbox
							closest_intersection = intersection
							closest_distance = detected_box.centroid.distance(expected_box.centroid)
					
				#if found, print out as hit, remove from expected and detected
				if closest_detected:
					results.write("{}\t1\t1\t{}\t{}\n".format(cascade_threshold,expected_box,Polygon(closest_detected)))
					detected.remove(closest_detected)
				#if not found, print out as false negative
				else:
					results.write("{}\t1\t0\t{}\t{}\n".format(cascade_threshold,expected_box,None))
			for bbox in detected:
				#detected should be pruned by now, so these are all false positives
				results.write("{}\t0\t1\t{}\t{}\n".format(cascade_threshold,None,Polygon(bbox)))

if __name__ == '__main__':
	main()
