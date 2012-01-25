<?php
	ini_set('memory_limit','1000M');
	/* SEE text-roc.py; Kevin says "JUST EW!"; Kaolin shrugs, and tries to hide the code. */
	$foo = file('results.txt');
	$accum = Array();
	foreach ($foo as $row) {
		list($parameter,$image,$expected,$detected) = explode("\t",$row);
		if (!isset($accum["".$paramater])) {
			//$accum["".$parameter] = Array ("falsepositive"=>0,"truepositive"=>0,"count"=>0);
		}
		if ($expected && $detected) {
			$accum["".$parameter]["truepositive"] ++;
		} else if (!$expected && $detected) {
			$accum["".$parameter]["falsepositive"] ++;
		} else if ($expected && !$detected) {
			$accum["".$parameter]["falsenegative"] ++;
		} else if (!$expected && !$detected) {
			$accum["".$parameter]["truenegative"] ++;
		}
	}
	// TPR = TP / P = TP / (TP + FN)
	// FPR = FP / N = FP / (FP + TN)
	foreach ($accum as $key=>$value) {
		$accum[$key]["tprate"] = $accum[$key]["truepositive"]/($accum[$key]["truepositive"] + $accum[$key]["falsenegative"]);
		$accum[$key]["fprate"] = $accum[$key]["falsepositive"]/($accum[$key]["falsepositive"] + $accum[$key]["truenegative"]);
	}
	print_r($accum);
