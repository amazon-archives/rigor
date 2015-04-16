from rigor.evaluator import ObjectAreaEvaluator
from shapely.geometry import Polygon
import numpy as np

kZeroAreaPolygon = Polygon(((1, 1), (11, 1), (11, 1), (1, 1)))
kNonZeroAreaPolygon = Polygon(((1, 1), (11, 1), (11, 11), (1, 11)))

kGroundTruth = (
	((2, 2), (9, 2), (9, 4), (2, 4)),
	((5, 7), (20, 7), (20, 11), (5, 11)),
	((3, 13), (11, 13), (11, 15), (3, 15)),
	((4, 16), (8, 16), (8, 19), (4, 19)),
	((9, 20), (12, 20), (12, 22), (9, 22)),
)

kDetected = (
	((13, 2), (19, 2), (19, 5), (13, 5)),
	((3, 7), (8, 7), (8, 11), (3, 11)),
	((10, 7), (20, 7), (20, 11), (10, 11)),
	((3, 13), (10, 13), (10, 19), (3, 19)),
	((9, 20), (12, 20), (12, 22), (9, 22)),
	((17, 17), (20, 17), (20, 20), (17, 20)),
	((17, 10), (19, 10), (19, 15), (17, 15)),
)

kGroundTruth2 = (
	((146, 169), (614, 169), (614, 371), (146, 371)),
	((22, 226), (108, 226), (108, 260), (22, 260)),
	((123, 235), (151, 235), (151, 251), (123, 251)),
	((166, 235), (202, 235), (202, 261), (166, 261)),
	((217, 228), (305, 228), (305, 258), (217, 258)),
)

kDetected2 = (
	((12, 264), (12, 221), (137, 221), (137, 264)),
	((139, 364), (139, 175), (534, 175), (534, 364)),
)

kMatchMatrixGroundTruth = np.array([
	[ 0., 0., 0., 0., 0., 0., 0.],
	[ 0., 0.6, 1., 0., 0., 0., 0.2],
	[ 0., 0., 0., 0.33333333, 0., 0., 0.],
	[ 0., 0., 0., 0.28571429, 0., 0., 0.],
	[ 0., 0., 0., 0., 1., 0., 0.],
])

kMatchMatrixDetections = np.array([
	[0., 0., 0., 0., 0., 0., 0.],
	[ 0., 0.2, 0.66666667, 0., 0., 0., 0.03333333],
	[ 0., 0., 0., 0.875, 0., 0., 0.],
	[ 0., 0., 0., 1., 0., 0., 0.],
	[ 0., 0., 0., 0., 1., 0., 0.],
])

kPrecisionMatrix = np.array([
	[1., 0., 0., 0., 0.,],
	[0., .3, 0., 0., 0.,],
	[0., .3, 1., 0., 0.,],
	[0., 0., 0., 1., 1.,],
])

kRecallMatrix = np.array([
	[1., 0., 0., 0., 0.,],
	[0., 1., 0., 0., 0.,],
	[0., 1., .2, 0., 0.,],
	[0., 0., 0., .3, .8,],
])

def test_non_zero_polygon_zero_area_no_warning(capfd):
	result = ObjectAreaEvaluator.non_zero_polygon(kZeroAreaPolygon, suppress_warning=True)
	out, err = capfd.readouterr()
	assert round(result.area, 3) == 1.005
	assert result.bounds == (0.95, 0.95, 11.05, 1.05)
	assert err == ''

def test_non_zero_polygon_zero_area_with_warning(capfd):
	result = ObjectAreaEvaluator.non_zero_polygon(kZeroAreaPolygon, suppress_warning=False)
	out, err = capfd.readouterr()
	assert round(result.area, 3) == 1.005
	assert result.bounds == (0.95, 0.95, 11.05, 1.05)
	assert len(err) > 0

def test_non_zero_polygon_nonzero_area():
	result = ObjectAreaEvaluator.non_zero_polygon(kNonZeroAreaPolygon)
	assert round(result.area, 3) == 100.0
	assert result.bounds == (1.0, 1.0, 11.0, 11.0)

def test_prune_and_polygon():
	gt_poly, det_poly = ObjectAreaEvaluator.prune_and_polygon(kGroundTruth, kDetected)
	assert [p.length for p in gt_poly] == [18.0, 38.0, 20.0, 14.0, 10.0]
	assert [p.length for p in det_poly] == [18.0, 18.0, 28.0, 26.0, 10.0, 12.0, 14.0]

def test_build_matrices():
	gt_poly, det_poly = ObjectAreaEvaluator.prune_and_polygon(kGroundTruth, kDetected)
	gt_matrix, det_matrix = ObjectAreaEvaluator.build_matrices(gt_poly, det_poly)
	assert np.allclose(gt_matrix, kMatchMatrixGroundTruth)
	assert np.allclose(det_matrix, kMatchMatrixDetections)

def test_evaluate():
	evaluator = ObjectAreaEvaluator()
	result = evaluator.evaluate(kGroundTruth, kDetected)
	assert result == (0.5714285714285714, 0.8, (4.0, 7.0), (4.0, 5.0))

def test_evaluate_no_detections():
	evaluator = ObjectAreaEvaluator()
	result = evaluator.evaluate(kGroundTruth, list())
	assert result == (0., 0., (0., 0.), (0., 5.))

def test_match_detections():
	evaluator = ObjectAreaEvaluator()
	result = evaluator.match_detections(kGroundTruth, kDetected)
	assert result == ([[], [1, 2], [3], [3], [4]], [[], [1], [1], [2, 3], [4], [], []])

def test_match_detections_no_detections():
	# TODO: is this the correct result?
	evaluator = ObjectAreaEvaluator()
	result = evaluator.match_detections(kGroundTruth, list())
	assert result == (0., 0., (0., 0.), (0., 5.))

#def test_evaluate_matrices():
#	evaluator = ObjectAreaEvaluator()
#	result = evaluator.evaluate_matrices(kPrecisionMatrix, kRecallMatrix)
#	assert result == (0.36, 0.65, (1.8, 5.0), (2.6, 4.0))
