import rigor.runner
import rigor.imageops
from rigor.database import Database
from rigor.dbmapper import DatabaseMapper

import argparse
import Image, ImageDraw

parameters = {
	"pyramid_step": 2,
	"pyramid_substep": 1.25,
	"pyramid_num_substeps": 5,
	"pyramid_min_width": 20,
	"pyramid_min_height": 10,
	"pyramid_window_width": 20,
	"pyramid_window_height": 10,
	"cluster_min_area": 600,
	"cluster_min_weight": 1.0
}

def main():
	parser = argparse.ArgumentParser(description='Runs text detector on relevant images')
	parser.add_argument('classifier_file', help='Path to classifier CLF')
	parser.add_argument('-l', '--limit', type=int, metavar='COUNT', required=False, help='Maximum number of images to use')
	parser.add_argument('-r', '--random', action="store_true", default=False, required=False, help='Fetch images ordered randomly if limit is active')
	args = parser.parse_args()
	parameters["classifier_file"] = args.classifier_file
	i = rigor.runner.Runner('text', parameters, args.limit, args.random)
	database_mapper = DatabaseMapper(Database())
	for result in i.run():
		detected = result[1]
		expected = result[2]
		image = database_mapper.get_image_by_id(result[0])
		pil_image = Image.open(rigor.imageops.fetch(image))
		draw = ImageDraw.Draw(pil_image)
		for bbox in expected:
			draw.polygon(bbox, outline='#0f0')
		for bbox in detected:
			draw.polygon(bbox, outline='#ff0')
		pil_image.save(".".join((str(image["id"]), image["format"])))

if __name__ == '__main__':
	main()
