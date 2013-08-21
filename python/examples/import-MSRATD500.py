""""
Script to import the set of MSRA-TD500 training/testing data into the rigor testing framework.
http://www.iapr-tc11.org/mediawiki/index.php/MSRA_Text_Detection_500_Database_(MSRA-TD500)
"""
from rigor.importer import Importer
import os
import glob
import string
import math
import copy

kExcludeHard = False
kDataType = "test" # "train" or "test"
kDataPath = '/home/kaolin/data/MSRA-TD500/{}/'.format(kDataType)
kDatabase = 'msratd500{}'.format(kDataType)
kBaseMetadata = {'source': 'MSRATD500',
	'tags': ["sample", "MSRATD500", "MSRATD500.{}".format(kDataType)] }
kImporter = Importer(kDataPath,kDatabase)
kDefaultAnnotationTag = {"annotation_tags" : ["annotated.by.MSRATD500"]}
kConfidence = 1
kAnnotationDomain = "text:line"

def main():
	for truthfile in glob.glob("{}*.gt".format(kDataPath)):
		#imagefile = "{}.JPG".format(string.rsplit(truthfile,'.',1)[0])
		#imagefile = string.join([string.rsplit(truthfile,'.',1)[0],'JPG'],'.')
		imagefile = truthfile.rsplit('.', 1)[0] + '.JPG' # simple is good :)
		local_image_path = os.path.split(imagefile)
		metadata = dict(kBaseMetadata)
		annotations = list()
		with open(truthfile,'r') as truth:
			for row in truth:
				(index,difficulty,x,y,w,h,rads) = string.split(row.rstrip())
				# tl, tr, br, bl
				rect = rotated_rect(int(x),int(y),int(w),int(h),float(rads))
				annotation = {"domain" : kAnnotationDomain, "confidence":kConfidence }
				annotation_tags = copy.deepcopy(kDefaultAnnotationTag)
				if difficulty == "0":
					difficulty = "difficulty.standard"
				else:
					if kExcludeHard:
						continue
					difficulty = "difficulty.hard"
				annotation_tags['annotation_tags'].append(difficulty)
				annotation.update(annotation_tags)
				annotation.update({'boundary':rect})
				annotation.update({'difficulty':difficulty})
				annotations.append(annotation)
		metadata.update({"annotations":annotations})
		image_name = local_image_path[1]
		metadata.update({"source_id":image_name})
		import_result = kImporter.import_image(imagefile, image_name, metadata)
		#import_result = None
		if import_result is None:
			# image already exists
			print(u'Error, image already exists: '.format(image_name))
		else:
			print(u'Successfully imported: {}'.format(image_name))

def rotated_rect(x,y,w,h,rads):
	s = math.sin(rads)
	c = math.cos(rads)
	mean_x = x + w / 2
	mean_y = y + h / 2
	w_2 = w/2
	h_2 = h/2
	tl = rotate_and_offset(-w_2,-h_2,s,c,mean_x,mean_y)
	tr = rotate_and_offset(w_2,-h_2,s,c,mean_x,mean_y)
	br = rotate_and_offset(w_2,h_2,s,c,mean_x,mean_y)
	bl = rotate_and_offset(-w_2,h_2,s,c,mean_x,mean_y)
	return [tl,tr,br,bl]

def rotate_and_offset(x, y, s, c, mx=0, my=0):
	return (x * c - y * s + mx, x * s + y * c + my)

if __name__ == "__main__":
	main()
