""" Algorithm evaluators for Rigor """

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

	def evaluate(self, ground_truths, detections):
		"""
		Given lists of polylines for each parameter (ground_truths, detections),
		this will check the overlap and return a (precision, recall, (sum_matchD,
		|D|), (sum_matchG, |G|)) tuple for the overall image.

		ground_truths and detections should both be sequences of (x,y) point tuples.
		"""
		if not ground_truths or not detections:
			return (0., 0., (0., 0.), (0., 0.))

		if not hasattr(ground_truths[0], 'intersection'):
			ground_truths = [self.Polygon(value) for value in ground_truths]
		if not hasattr(detections[0], 'intersection'):
			detections = [self.Polygon(value) for value in detections]

		ground_truth_count = len(ground_truths)
		detection_count = len(detections)

		recall_matrix = self.np.empty((ground_truth_count, detection_count), dtype=float)
		precision_matrix = self.np.empty((ground_truth_count, detection_count), dtype=float)

		row_counts_precision = [0] * ground_truth_count # number of items in the row of the precision matrix that are greater than the threshold
		column_counts_precision = [0] * detection_count # number of items in the column of the precision matrix that are greater than the threshold
		row_counts_recall = [0] * ground_truth_count # number of items in the row of the recall matrix that are greater than the threshold
		column_counts_recall = [0] * detection_count # number of items in the column of the recall matrix that are greater than the threshold
		row_sums_precision = [0.] * ground_truth_count # sum of items in the row of the precision matrix that are greater than the threshold
		column_sums_precision = [0.] * detection_count # sum of items in the column of the precision matrix that are greater than the threshold
		row_sums_recall = [0.] * ground_truth_count # sum of items in the row of the recall matrix that are greater than the threshold
		column_sums_recall = [0.] * detection_count # sum of items in the column of the recall matrix that are greater than the threshold

		match_ground_truth = 0. # sum of MatchG
		match_detection = 0. # sum of MatchD

		for gt_index in range(0, ground_truth_count):
			ground_truth = ground_truths[gt_index]
			for det_index in range(0, detection_count):
				detection = detections[det_index]
				overlap_polygon = ground_truth.intersection(detection)

				precision_area = overlap_polygon.area / detection.area
				precision_matrix[gt_index, det_index] = precision_area
				if precision_area > self.precision_threshold:
					column_counts_precision[det_index] += 1
					row_counts_precision[gt_index] += 1
					column_sums_precision[det_index] += precision_area
					row_sums_precision[gt_index] += precision_area

				recall_area = overlap_polygon.area / ground_truth.area
				recall_matrix[gt_index, det_index] = recall_area
				if recall_area > self.recall_threshold:
					column_counts_recall[det_index] += 1
					row_counts_recall[gt_index] += 1
					column_sums_recall[det_index] += recall_area
					row_sums_recall[gt_index] += recall_area
			# Detection row has been computed for this ground truth entry. We can
			# look for one-to-many matches (splits)
			if row_counts_precision[gt_index] > 1 and row_sums_precision[gt_index] > self.recall_threshold:
				match_ground_truth += self.scatter_punishment(row_counts_precision[gt_index])
		# Got splits and sums and counts. Traverse columns and get merges
		for det_index in range(0, detection_count):
			if column_counts_recall[det_index] > 1 and column_sums_recall[det_index] > self.precision_threshold:
				match_detection += self.scatter_punishment(column_counts_recall[det_index])
		# And, finally, one-to-one matches
		for gt_index in range(0, ground_truth_count):
			if row_counts_precision[gt_index] == 1 and row_counts_recall[gt_index] == 1:
				for det_index in range(0, detection_count):
					if column_counts_precision[det_index] == 1 and column_counts_recall[det_index] == 1:
						if precision_matrix[gt_index, det_index] > self.precision_threshold and recall_matrix[gt_index, det_index] > self.recall_threshold:
							match_ground_truth += 1
							match_detection += 1
		recall = match_ground_truth / float(ground_truth_count)
		precision = match_detection / float(detection_count)
		return (precision, recall, (match_detection, float(detection_count)), (match_ground_truth, float(ground_truth_count)))
