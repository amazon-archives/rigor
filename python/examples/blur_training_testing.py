"""
Selects images from the blur domain, and writes a file for blur/noblur training and testing with image locations.
Uses argparse, run blur_training_testing w/o inputs or with --help for valid arguments
Uses Same basic parameters for limiting/including images
e.g., python blur_training_testing.py --tag_require sightpal
"""

from rigor.database import Database
from rigor.dbmapper import DatabaseMapper
import rigor.imageops

import argparse
import random

kDomain = 'blur'

def main():
	training_file = open('training.txt','w')
	testing_file = open('testing.txt','w')
	training_images = {'blur':list(), 'noblur':list()}
	testing_images = {'blur':list(), 'noblur':list()}
	parser = argparse.ArgumentParser(description='generates training/testing files for blur')
	parser.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	parser.add_argument('--tag_require', action='append', dest='tags_require', default=None, required=False, help='Tag that must be present on selected images')
	parser.add_argument('--tag_exclude', action='append', dest='tags_exclude', default=None, required=False, help='Tag that must not be present on selected images')
	parser.add_argument('-p', '--percent_training', dest='percent', default=0.25, required=False, help='Tag indicating what percent of images for training')
	args = parser.parse_args()
	db = Database()
	db_mapper = DatabaseMapper(db)
	images = db_mapper.get_images_for_analysis(kDomain, limit=args.limit, random=args.random, tags_require=args.tags_require, tags_exclude=args.tags_exclude)
	blur_images = list()
	noblur_images = list()
	for image in images:
		if image['annotations'][0]['model'] == 'blur':
			blur_images.append(image)
		else:
			noblur_images.append(image)
	random.shuffle(blur_images)
	random.shuffle(noblur_images)
	blur_training_len = int(len(blur_images)*float(args.percent))
	noblur_training_len = int(len(noblur_images)*float(args.percent))
	training_images['blur'] = blur_images[:blur_training_len]
	testing_images['blur'] = blur_images[blur_training_len:]
	training_images['noblur'] = noblur_images[:noblur_training_len]
	testing_images['noblur'] = noblur_images[noblur_training_len:]
	for file,image_dict in ((training_file,training_images),(testing_file,testing_images)):
		for model in image_dict.keys():
			for image in image_dict[model]:
				file.write('{}\t{}\n'.format(rigor.imageops.find(image), model))

if __name__ == '__main__':
	main()
