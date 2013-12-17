""" Algorithm evaluators for Rigor """

from __future__ import print_function
from collections import defaultdict
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

	def __init__(self, scatter_punishment=lambda(k): 1.0, precision_threshold=0.4, recall_threshold=0.8):
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
	def non_zero_polygon(polygon, suppress_warning=False):
		"""
		Checks that a polygon has a nonzero area. If the area is zero, it will be
		dilated by a small amount so that overlap and such can be measured.

		>>> from shapely.geometry import Polygon
		>>> zero_area = Polygon(((1, 1), (11, 1), (11, 1), (1, 1)))
		>>> result = ObjectAreaEvaluator.non_zero_polygon(zero_area, suppress_warning=True)
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

		if not suppress_warning:
			print("Warning: polygon has zero area; dilating", file=sys.stderr)
		return polygon.buffer(0.05, 1).convex_hull

	@classmethod
	def prune_and_polygon(cls, ground_truths, detections):
		"""
		Given either shapely.Polygon instances or plain-Python sequences of
		vertices, returns a tuple of ground truth and detection shapely.Polygon
		instances, excluding ground truth polygons that have zero length

		>>> gt_poly, det_poly = ObjectAreaEvaluator.prune_and_polygon(gt, det)
		>>> [p.length for p in gt_poly]
		[18.0, 38.0, 20.0, 14.0, 10.0]
		>>> [p.length for p in det_poly]
		[18.0, 18.0, 28.0, 26.0, 10.0, 12.0, 14.0]
		"""
		if not hasattr(ground_truths[0], 'intersection'):
			ground_truths = [cls.Polygon(value) for value in ground_truths]
		if not hasattr(detections[0], 'intersection'):
			detections = [cls.Polygon(value) for value in detections]
		ground_truths = [value for value in ground_truths if value.length > 0.]
		return (ground_truths, detections)

	@classmethod
	def build_matrices(cls, ground_truths, detections):
		"""
		Builds a set of matrices containing measurements of overlap between ground
		truth and detections.

		>>> gt_poly, det_poly = ObjectAreaEvaluator.prune_and_polygon(gt, det)
		>>> ObjectAreaEvaluator.build_matrices(gt_poly, det_poly)
		(array([[ 0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
		         0.        ,  0.        ],
		       [ 0.        ,  0.6       ,  1.        ,  0.        ,  0.        ,
		         0.        ,  0.2       ],
		       [ 0.        ,  0.        ,  0.        ,  0.33333333,  0.        ,
		         0.        ,  0.        ],
		       [ 0.        ,  0.        ,  0.        ,  0.28571429,  0.        ,
		         0.        ,  0.        ],
		       [ 0.        ,  0.        ,  0.        ,  0.        ,  1.        ,
		         0.        ,  0.        ]]), array([[ 0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
		         0.        ,  0.        ],
		       [ 0.        ,  0.2       ,  0.66666667,  0.        ,  0.        ,
		         0.        ,  0.03333333],
		       [ 0.        ,  0.        ,  0.        ,  0.875     ,  0.        ,
		         0.        ,  0.        ],
		       [ 0.        ,  0.        ,  0.        ,  1.        ,  0.        ,
		         0.        ,  0.        ],
		       [ 0.        ,  0.        ,  0.        ,  0.        ,  1.        ,
		         0.        ,  0.        ]]))
		"""
		ground_truth_count = len(ground_truths)
		detection_count = len(detections)

		recall_matrix = cls.np.empty((ground_truth_count, detection_count), dtype=float)
		precision_matrix = cls.np.empty((ground_truth_count, detection_count), dtype=float)

		for gt_index in range(ground_truth_count):
			ground_truth = ObjectAreaEvaluator.non_zero_polygon(ground_truths[gt_index])
			for det_index in range(detection_count):
				detection = ObjectAreaEvaluator.non_zero_polygon(detections[det_index])
				overlap_polygon = ground_truth.intersection(detection)

				precision_area = overlap_polygon.area / detection.area
				precision_matrix[gt_index, det_index] = precision_area
				recall_area = overlap_polygon.area / ground_truth.area
				recall_matrix[gt_index, det_index] = recall_area
		return (precision_matrix, recall_matrix)

	def match_detections(self, ground_truths, detections):
		"""
		gt_to_detections, detections_to_gt = evaluator.match_detections(ground_truths, detections)
		debugDetail('gt to detection matches: %s' % str(gt_to_detections))
		debugDetail('detection to gt matches: %s' % str(detections_to_gt))
		return (
			( False, (1, 2), (3, 5), (4,), (6,),  (6,) ),
			( (2,), (2,), (3,), (4,), (3,), (5, 6))
		)
		"""
		if not ground_truths or not detections:
			return (0.,0.,(0.,len(detections)), (0., len(ground_truths)))

		ground_truths, detections = ObjectAreaEvaluator.prune_and_polygon(ground_truths, detections)
		ground_truth_count = len(ground_truths)
		detection_count = len(detections)
		if ground_truth_count == 0 or detection_count == 0:
			return (0., 0., (0., float(detection_count)), (0., float(ground_truth_count)))

		precision_matrix, recall_matrix = self.build_matrices(ground_truths, detections)
		ground_truth_count = precision_matrix.shape[0]
		detection_count = precision_matrix.shape[1]
		ground_truth_sets_precision = defaultdict(set) # number of ground truth items that match a particular detection in the precision matrix
		detection_sets_precision = defaultdict(set) # number of detection items that match a particular ground truth in the precision matrix
		ground_truth_sets_recall = defaultdict(set) # number of ground truth items that match a particular detection in the recall matrix
		detection_sets_recall = defaultdict(set) # number of detection items that match a particular ground truth in the recall matrix

		for gt_index in range(ground_truth_count):
			for det_index in range(detection_count):
				if precision_matrix[gt_index, det_index] >= self.precision_threshold:
					ground_truth_sets_precision[det_index].add(gt_index)
					detection_sets_precision[gt_index].add(det_index)
				if recall_matrix[gt_index, det_index] >= self.recall_threshold:
					ground_truth_sets_recall[det_index].add(gt_index)
					detection_sets_recall[gt_index].add(det_index)

		match_ground_truth =  [[] for number in xrange(ground_truth_count)]
		match_detection = [[] for number in xrange(detection_count)]

		for gt_index in detection_sets_precision:
			matching_detections_precision = detection_sets_precision[gt_index]
			if len(matching_detections_precision) == 1:
				(detection_precision, ) = matching_detections_precision
				if len(ground_truth_sets_precision[detection_precision]) == 1:
					match_ground_truth[gt_index].append(detection_precision)
			else:
				# one-to-many (one ground truth to many detections)
				gt_sum = 0.
				for detection_precision in matching_detections_precision:
					gt_sum += recall_matrix[gt_index, detection_precision]
				if gt_sum >= self.recall_threshold:
					for detection_precision in matching_detections_precision:
						match_ground_truth[gt_index].append(detection_precision)
						match_detection[detection_precision].append(gt_index)
		for det_index in ground_truth_sets_recall:
			matching_ground_truths_recall = ground_truth_sets_recall[det_index]
			if len(matching_ground_truths_recall) == 1:
				(ground_truth_recall, ) = matching_ground_truths_recall
				if len(detection_sets_recall[ground_truth_recall]) == 1:
					match_detection[det_index].append(ground_truth_recall)
			else:
				# many-to-one (many ground truths covered by one detection)
				det_sum = 0
				for ground_truth_recall in matching_ground_truths_recall:
					det_sum += precision_matrix[ground_truth_recall, det_index]
				if det_sum >= self.precision_threshold:
					for ground_truth_recall in matching_ground_truths_recall:
						det_sum += precision_matrix[ground_truth_recall, det_index]
						match_detection[det_index].append(ground_truth_recall)
						match_ground_truth[ground_truth_recall].append(det_index)
		return match_ground_truth, match_detection

	def evaluate(self, ground_truths, detections):
		"""
		Given lists of polylines for each parameter (ground_truths, detections),
		this will check the overlap and return a (precision, recall, (sum_matchD,
		|D|), (sum_matchG, |G|)) tuple for the overall image.

		ground_truths and detections should both be sequences of (x,y) point tuples.

		>>> e = ObjectAreaEvaluator()
		>>> e.evaluate(gt, det)
		(0.5714285714285714, 0.8, (4.0, 7.0), (4.0, 5.0))
		"""

		if not ground_truths or not detections:
			return (0.,0.,(0.,len(detections)), (0., len(ground_truths)))

		ground_truths, detections = ObjectAreaEvaluator.prune_and_polygon(ground_truths, detections)
		ground_truth_count = len(ground_truths)
		detection_count = len(detections)
		if ground_truth_count == 0 or detection_count == 0:
			return (0., 0., (0., float(detection_count)), (0., float(ground_truth_count)))

		precision_matrix, recall_matrix = self.build_matrices(ground_truths, detections)
		return self.evaluate_matrices(precision_matrix, recall_matrix)

	def evaluate_matrices(self, precision_matrix, recall_matrix):
		"""
		Given a precision and recall matrix (2d matrix; rows are ground truth,
		columns are detections) containing overlap between each pair of ground
		truth and detection polygons, this will run the match functions over the
		matrix and return a (precision, recall, (sum_matchD, |D|), (sum_matchG,
		|G|)) tuple for the overall image.

		>>> e = ObjectAreaEvaluator()
		>>> precision = e.np.array([[ 1., 0., 0., 0., 0.,], \
			[0., .3, 0., 0., 0.,], \
			[0., .3, 1., 0., 0.,], \
			[0., 0., 0., 1., 1.,], \
			])
		>>> recall = e.np.array([[1., 0., 0., 0., 0.,], \
			[0., 1., 0., 0., 0.,], \
			[0., 1., .2, 0., 0.,], \
			[0., 0., 0., .3, .8,], \
			])
		>>> e.evaluate_matrices(precision, recall)
		(0.36, 0.65, (1.8, 5.0), (2.6, 4.0))
		"""
		ground_truth_count = precision_matrix.shape[0]
		detection_count = precision_matrix.shape[1]
		ground_truth_sets_precision = defaultdict(set) # number of ground truth items that match a particular detection in the precision matrix
		detection_sets_precision = defaultdict(set) # number of detection items that match a particular ground truth in the precision matrix
		ground_truth_sets_recall = defaultdict(set) # number of ground truth items that match a particular detection in the recall matrix
		detection_sets_recall = defaultdict(set) # number of detection items that match a particular ground truth in the recall matrix

		for gt_index in range(ground_truth_count):
			for det_index in range(detection_count):
				if precision_matrix[gt_index, det_index] >= self.precision_threshold:
					ground_truth_sets_precision[det_index].add(gt_index)
					detection_sets_precision[gt_index].add(det_index)
				if recall_matrix[gt_index, det_index] >= self.recall_threshold:
					ground_truth_sets_recall[det_index].add(gt_index)
					detection_sets_recall[gt_index].add(det_index)

		match_ground_truth = 0. # sum of MatchG
		match_detection = 0. # sum of MatchD

		one_to_one_precision = set()
		for gt_index in detection_sets_precision:
			matching_detections_precision = detection_sets_precision[gt_index]
			if len(matching_detections_precision) == 1:
				(detection_precision, ) = matching_detections_precision
				if len(ground_truth_sets_precision[detection_precision]) == 1:
					one_to_one_precision.add((gt_index, detection_precision))
			else:
				# one-to-many (one ground truth to many detections)
				gt_sum = 0.
				for detection_precision in matching_detections_precision:
					gt_sum += recall_matrix[gt_index, detection_precision]
				if gt_sum >= self.recall_threshold:
					#print("1:N ~ GT {} : DT {}".format(gt_index,matching_detections_precision))
					match_ground_truth += self.scatter_punishment(matching_detections_precision)
					match_detection += len(matching_detections_precision) * self.scatter_punishment(matching_detections_precision)

		one_to_one_recall = set()
		for det_index in ground_truth_sets_recall:
			matching_ground_truths_recall = ground_truth_sets_recall[det_index]
			if len(matching_ground_truths_recall) == 1:
				(ground_truth_recall, ) = matching_ground_truths_recall
				if len(detection_sets_recall[ground_truth_recall]) == 1:
					one_to_one_recall.add((ground_truth_recall, det_index))
			else:
				# many-to-one (many ground truths covered by one detection)
				det_sum = 0
				for ground_truth_recall in matching_ground_truths_recall:
					det_sum += precision_matrix[ground_truth_recall, det_index]
				if det_sum >= self.precision_threshold:
					#print("N:1 ~ DT {} : GT {}".format(det_index,matching_ground_truths_recall))
					match_detection += self.scatter_punishment(matching_ground_truths_recall)
					match_ground_truth += len(matching_ground_truths_recall) * self.scatter_punishment(matching_ground_truths_recall)

		one_to_one_matches = one_to_one_precision & one_to_one_recall
		match_ground_truth += len(one_to_one_matches)
		match_detection += len(one_to_one_matches)

		recall = match_ground_truth / float(ground_truth_count)
		precision = match_detection / float(detection_count)
		return (precision, recall, (match_detection, float(detection_count)), (match_ground_truth, float(ground_truth_count)))

if __name__ == '__main__':
	import doctest
	doctest.testmod(extraglobs = {
		'gt': (
			((2, 2), (9, 2), (9, 4), (2, 4)),
			((5, 7), (20, 7), (20, 11), (5, 11)),
			((3, 13), (11, 13), (11, 15), (3, 15)),
			((4, 16), (8, 16), (8, 19), (4, 19)),
			((9, 20), (12, 20), (12, 22), (9, 22)),
		),
		'det': (
			((13, 2), (19, 2), (19, 5), (13, 5)),
			((3, 7), (8, 7), (8, 11), (3, 11)),
			((10, 7), (20, 7), (20, 11), (10, 11)),
			((3, 13), (10, 13), (10, 19), (3, 19)),
			((9, 20), (12, 20), (12, 22), (9, 22)),
			((17, 17), (20, 17), (20, 20), (17, 20)),
			((17, 10), (19, 10), (19, 15), (17, 15)),
		),
		'gt2':  [[(146, 169), (614, 169), (614, 371), (146, 371)], [(22, 226), (108, 226), (108, 260), (22, 260)], [(123, 235), (151, 235), (151, 251), (123, 251)], [(166, 235), (202, 235), (202, 261), (166, 261)], [(217, 228), (305, 228), (305, 258), (217, 258)]],
		'det2': [((12, 264), (12, 221), (137, 221), (137, 264)), ((139, 364), (139, 175), (534, 175), (534, 364))],
	})
