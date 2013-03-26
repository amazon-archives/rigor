""""
Script to Import the set of ICDAR2003 training/testing data into the rigor testing framework.
http://algoval.essex.ac.uk/icdar/Datasets.html
Reads the xml file with annotations and imports into database with the given annotations
"""
from rigor.importer import Importer
import os
from bs4 import BeautifulSoup

kDataPath = '/Users/dave/dev/dave_python_testing/SceneTrialTrain/'
kMetadataFile = 'words.xml'
kBaseMetadata = {'source': 'ICDAR2003',
	'tags': ["sample", "ICDAR2003", "ICDAR2003.sample", "single_words"]}
kImporter = Importer(kDataPath)
kDefaultAnnotationTag = {"annotation_tags" : ["annotated.by.ICDAR2003"]}
kConfidence = 1

def main():
	with open(os.path.join(kDataPath, 'words.xml')) as source_metadata:
		soup = BeautifulSoup(source_metadata,"lxml")
		#print(soup.prettify())

	for image in soup.tagset.find_all('image'):
		#print(image.imagename).text
		resolution_x = image.resolution.attrs['x']
		resolution_y = image.resolution.attrs['y']
		metadata = dict(kBaseMetadata)
		annotations = list()
		for roi in image.taggedrectangles.find_all('taggedrectangle'):
			annotation = {"domain" : "text"}
			annotation.update({"model" : roi.tag.text})
			annotation.update(kDefaultAnnotationTag)
			#boundary_coords = rectangle_with_offset(roi)
			boundary_coords = rectangle_no_offset(roi)
			annotation.update({'boundary':boundary_coords})
			annotation.update({'confidence':kConfidence})
			annotations.append(annotation)
		metadata.update({"annotations":annotations})
		#print(metadata)
		local_image_path = os.path.split(image.imagename.text)
		image_path = os.path.join(kDataPath, image.imagename.text)
		image_name = local_image_path[1]
		import_result = kImporter.import_image(image_path, image_name, metadata)
		if import_result is None:
			# image already exists
			print(u'Error, image already exists: '+image.name)
		else:
			print(u'Successfully imported: '+image.name)

def rectangle_with_offset(roi):
	"""
	takes a rectangle from ICDAR 2003, and imports it 
	"""
	top_left_x = int(float(roi.attrs['x']))
	top_left_y = int(float(roi.attrs['y']))
	width = int(float(roi.attrs['width']))
	height = int(float(roi.attrs['height']))
	offset = int(float(roi.attrs['offset']))
	top_left = (top_left_x, top_left_y)
	top_right = (min(top_left_x+width,resolution_x), top_left_y)
	bottom_right = (min(top_left_x+width-offset, resolution_x), min(top_left_y+height, resolution_y))
	bottom_left = (max(top_left_x-offset, 0), min(top_left_y+height, resolution_y))
	return [top_left, top_right, bottom_right, bottom_left]

def rectangle_no_offset(roi):
	"""
	takes a rectangle from ICDAR 2003, and imports it 
	"""
	top_left_x = int(float(roi.attrs['x']))
	top_left_y = int(float(roi.attrs['y']))
	width = int(float(roi.attrs['width']))
	height = int(float(roi.attrs['height']))
	top_left = (top_left_x, top_left_y)
	top_right = (min(top_left_x+width,resolution_x), top_left_y)
	bottom_right = (min(top_left_x+width, resolution_x), min(top_left_y+height, resolution_y))
	bottom_left = (max(top_left_x, 0), min(top_left_y+height, resolution_y))
	return [top_left, top_right, bottom_right, bottom_left]
	
if __name__ == "__main__":
	main()


