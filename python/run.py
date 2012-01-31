import rigor.runner

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt

def main():
	parser = argparse.ArgumentParser(description='Runs algorithm on relevant images')
	parser.add_argument('domain', help='Domain to run')
	parser.add_argument('parameters', help='Path to parameters file, or JSON block containing parameters')
	parser.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	args = parser.parse_args()
	try:
		parameters = json.loads(args.parameters)
	except ValueError:
		try:
			with open(args.parameters, 'rb') as param_file:
				parameters = json.load(param_file)
		except ValueError:
			parameters = args.parameters
	i = rigor.runner.Runner(args.domain, parameters, args.limit, args.random)

	# COMPUTING ROC VALUES
	similarity_values = [0.03, 0.05, 0.07, 0.09, 0.11]
	low_freq_rate_values = [0.94, 0.96, 0.98]
	tpr_list_all = []	# True positive rate list for all similarity value
	fpr_list_all = []	# True positive rate list for all similarity value
	roclabel = []	# ROC labels

	for lfr_index in range(len(low_freq_rate_values)):
		tpr_list = []	# True positive rate list for each similarity value
		fpr_list = []	# False positive rate list for each similarity value
		for similarity_index in range(len(similarity_values)):		
			tp = fn = tn = fp = 0 # true and false positive and negative counters
			for result in i.run():
				# print("\t".join([str(x) for x in result]))
				blur_estim = (float(result[1][1]) < similarity_values[similarity_index]) or (float(result[1][0]) > low_freq_rate_values[lfr_index])
				if result[2] == "blur":
					if blur_estim:
						tp = tp + 1
					else:
						fn = fn + 1
				else:
					if blur_estim:
						fp = fp + 1
					else:
						tn = tn + 1
			# print 'tp {0}, fp {1}, tn {2}, fn {3}'.format(tp, fp, tn, fn)

			if (tp + fn) > 0:
				true_positive_rate = float(tp)/(tp+fn)
			else:
				true_positive_rate = 0.0
			if (tn + fp) > 0:
				false_positive_rate = float(fp)/(tn+fp)
			else:
				false_positive_rate = 0.0
			# print 'ROC values: ({0:3f}, {1:3f})'.format(true_positive_rate, false_positive_rate)
			tpr_list = tpr_list + [true_positive_rate]
			fpr_list = fpr_list + [false_positive_rate]
		tpr_list_all = tpr_list_all + [tpr_list]
		fpr_list_all = fpr_list_all + [fpr_list]

	# PLOTTING ROC VALUES
	fig1 = plt.figure()
	for lfr_index in range(len(low_freq_rate_values)):
		buf = 'Low Freq Rate Thresh = %.2f' % (low_freq_rate_values[lfr_index])
		roclabel = roclabel + [buf]
		plt.text(fpr_list_all[lfr_index][0], tpr_list_all[lfr_index][0] - 0.01,'%.3f' % similarity_values[0])
		plt.text(fpr_list_all[lfr_index][len(similarity_values)-1], tpr_list_all[lfr_index][len(similarity_values)-1] - 0.01,'%.3f' % similarity_values[len(similarity_values)-1])

	plt.plot(zip(*fpr_list_all), zip(*tpr_list_all), '*-')	# Transpose of both matrices
	plt.xlim(0, 0.4)
	plt.ylim(0.6, 1)
	plt.xlabel('False Positive Rate: fp/(tn+fp)')
	plt.ylabel('True Positive Rate: tp/(tp+fn)')
	title = 'ROC curves for the Blur Detector using %d images' % (tp + tn + fp + fn)
	plt.title(title)
	plt.legend(roclabel, 'lower right')
	plt.grid()
	fig1.savefig("ROC.png")


if __name__ == '__main__':
	main()
