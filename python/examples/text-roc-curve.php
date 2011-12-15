<?php
	/* SEE text-roc.py; Kevin says "JUST EW!"; Kaolin shrugs, and tries to hide the code. */
	$foo = file('../results/results.txt');
	$accum = Array();
	foreach ($foo as $row) {
		list($parameter,$expected,$detected) = explode("\t",$row);
		if (!isset($accum["".$paramater])) {
			//$accum["".$parameter] = Array ("falsepositive"=>0,"truepositive"=>0,"count"=>0);
		}
		if ($expected && $detected) {
			$accum["".$parameter]["truepositive"] ++;
			$accum["".$parameter]["count"] ++;
		} else if (!$expected && $detected) {
			$accum["".$parameter]["falsepositive"] ++;
		} else if ($expected && !$detected) {
			$accum["".$parameter]["count"] ++;
		}
	}
	foreach ($accum as $key=>$value) {
		if ($value["count"] == 0) $value["count"] = 1;
		$accum[$key]["tprate"] = $accum[$key]["truepositive"]/$value["count"];
		$accum[$key]["fprate"] = $accum[$key]["falsepositive"]/$value["count"];
	}
	print_r($accum);
