import rigor.database
import rigor.imageops

from rigor.dbmapper import DatabaseMapper
from rigor.config import config

import psycopg2

gDb = rigor.database.Database()
gDbMapper = DatabaseMapper(gDb)

def main():
	source_to_delete ='ICDAR2003'
	images = gDbMapper.get_images_by_source(source_to_delete)
	print('Found {0} images'.format(len(images)))
	for image in images:
		print('testing: not deleteing image id {0}'.format(image['id']))
		#rigor.imageops.destroy_image(gDb, image)

if __name__ == "__main__":
	main()


