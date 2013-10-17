""" Algorithm evaluators for Rigor """

from __future__ import print_function
import sys

class ObjectAreaEvaluator(object):
	"""
	Compares ground truth to detections using Wolf and Jolion's algorithm.

	For more information, see Object count/Area Graphs for the Evaluation of
	Object Detection and Segmentation Algorithms at
	[1] http://liris.cnrs.fr/Documents/Liris-2216.pdf
	"""
	import numpy as np
	from shapely.geometry import Polygon

	def __init__(self, scatter_punishment=lambda(k): 0.8, precision_threshold=0.4, recall_threshold=0.8):
		"""
		scatter_punishment is f_{sc}(k); "a parameter function of the evaluation
		scheme which controls the amount of punishment which is inflicted in case
		of scattering, i.e. splits or merges"

		precision_threshold is t_{p} in [1]
		recall_threshold is t_{r} in [1]
		"""
		self.scatter_punishment = scatter_punishment
		self.precision_threshold = precision_threshold
		self.recall_threshold = recall_threshold

	@staticmethod
	def non_zero_polygon(polygon):
		"""
		Checks that a polygon has a nonzero area. If the area is zero, it will be
		dilated by a small amount so that overlap and such can be measured.

		>>> from shapely.geometry import Polygon
		>>> zero_area = Polygon(((1, 1), (11, 1), (11, 1), (1, 1)))
		>>> result = ObjectAreaEvaluator.non_zero_polygon(zero_area)
		>>> round(result.area, 3)
		1.005
		>>> result.bounds
		(0.95, 0.95, 11.05, 1.05)
		>>> nonzero_area = Polygon(((1, 1), (11, 1), (11, 11), (1, 11)))
		>>> result = ObjectAreaEvaluator.non_zero_polygon(nonzero_area)
		>>> round(result.area, 3)
		100.0
		>>> result.bounds
		(1.0, 1.0, 11.0, 11.0)
		"""
		if polygon.area > 0:
			return polygon

		print("Warning: polygon has zero area; dilating", file=sys.stderr)
		return polygon.buffer(0.05, 1).convex_hull

	def match_detections(self, ground_truths, detections):
		return (
			( False, (1, 2), (3, 5), (4,), (6,),  (6,) ),
			( (2,), (2,), (3,), (4,), (3,), (5, 6))
		)

	def evaluate(self, ground_truths, detections):
		"""
		Given lists of polylines for each parameter (ground_truths, detections),
		this will check the overlap and return a (precision, recall, (sum_matchD,
		|D|), (sum_matchG, |G|)) tuple for the overall image.

		ground_truths and detections should both be sequences of (x,y) point tuples.

		>>> gt = (
		... ((2, 2), (9, 2), (9, 4), (2, 4)),
		... ((5, 7), (20, 7), (20, 11), (5, 11)),
		... ((3, 13), (11, 13), (11, 15), (3, 15)),
		... ((4, 16), (8, 16), (8, 19), (4, 19)),
		... ((9, 20), (12, 20), (12, 22), (9, 22)),
		... )
		>>> det = (
		... ((13, 2), (19, 2), (19, 5), (13, 5)),
		... ((3, 7), (8, 7), (8, 11), (3, 11)),
		... ((10, 7), (20, 7), (20, 11), (10, 11)),
		... ((3, 13), (10, 13), (10, 19), (3, 19)),
		... ((9, 20), (12, 20), (12, 22), (9, 22)),
		... ((17, 17), (20, 17), (20, 20), (17, 20)),
		... ((17, 10), (19, 10), (19, 15), (17, 15)),
		... )
		>>> e = ObjectAreaEvaluator()
		>>> e.evaluate(gt, det)
		(0.5428571428571428, 0.76, (3.8, 7.0), (3.8, 5.0))
		"""
		if not ground_truths or not detections:
			return (0., 0., (0., 0.), (0., 0.))

		if not hasattr(ground_truths[0], 'intersection'):
			ground_truths = [self.Polygon(value) for value in ground_truths]
		if not hasattr(detections[0], 'intersection'):
			detections = [self.Polygon(value) for value in detections]

		ground_truths = [value for value in ground_truths if value.length > 0.]

		ground_truth_count = len(ground_truths)
		detection_count = len(detections)

		if ground_truth_count == 0:
			return (float('nan'), float('nan'), (float('nan'), float(detection_count)), (float('nan'), float(ground_truth_count)))

		recall_matrix = self.np.empty((ground_truth_count, detection_count), dtype=float)
		precision_matrix = self.np.empty((ground_truth_count, detection_count), dtype=float)

		row_counts_precision = [0] * ground_truth_count # number of items in the row of the precision matrix that are greater than the threshold
		column_counts_precision = [0] * detection_count # number of items in the column of the precision matrix that are greater than the threshold
		row_counts_recall = [0] * ground_truth_count # number of items in the row of the recall matrix that are greater than the threshold
		column_counts_recall = [0] * detection_count # number of items in the column of the recall matrix that are greater than the threshold
		column_sums_precision = [0.] * detection_count # sum of items in the column of the precision matrix that are greater than the threshold
		row_sums_recall = [0.] * ground_truth_count # sum of items in the row of the recall matrix that are greater than the threshold

		match_ground_truth = 0. # sum of MatchG
		match_detection = 0. # sum of MatchD

		for gt_index in range(0, ground_truth_count):
			ground_truth = ObjectAreaEvaluator.non_zero_polygon(ground_truths[gt_index])
			for det_index in range(0, detection_count):
				detection = ObjectAreaEvaluator.non_zero_polygon(detections[det_index])
				overlap_polygon = ground_truth.intersection(detection)

				precision_area = overlap_polygon.area / detection.area
				precision_matrix[gt_index, det_index] = precision_area
				recall_area = overlap_polygon.area / ground_truth.area
				recall_matrix[gt_index, det_index] = recall_area

				if precision_area > self.precision_threshold:
					column_counts_precision[det_index] += 1
					row_counts_precision[gt_index] += 1
					row_sums_recall[gt_index] += recall_area
				if recall_area > self.recall_threshold:
					column_counts_recall[det_index] += 1
					row_counts_recall[gt_index] += 1
					column_sums_precision[det_index] += precision_area
			# Detection row has been computed for this ground truth entry. We can
			# look for one-to-many matches (splits)
			if row_counts_recall[gt_index] == 1:
				match_ground_truth += 1
			elif row_counts_precision[gt_index] > 1 and row_sums_recall[gt_index] > self.recall_threshold:
				match_ground_truth += self.scatter_punishment(row_counts_recall[gt_index])
		# Got splits and sums and counts. Traverse columns and get merges
		for det_index in range(0, detection_count):
			if column_counts_precision[det_index] == 1:
				match_detection += 1
			elif column_counts_recall[det_index] > 1 and column_sums_precision[det_index] > self.precision_threshold:
				match_detection += self.scatter_punishment(column_counts_precision[det_index])

		recall = match_ground_truth / float(ground_truth_count)
		precision = match_detection / float(detection_count)
		return (precision, recall, (match_detection, float(detection_count)), (match_ground_truth, float(ground_truth_count)))
