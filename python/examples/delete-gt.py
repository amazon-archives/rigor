""""
Script to delete ground truth (image, thumbnail, and all!)
"""
import rigor.imageops
from rigor.dbmapper import DatabaseMapper
from rigor.database import Database

# delete_ids = (18951,18953,18955)

db = Database()
db_mapper = DatabaseMapper(db)
for image_id in delete_ids:
	image = db_mapper.get_image_by_id(image_id)
	print "OBLITERATING {}".format(image['id'])
	rigor.imageops.destroy_image(db, image)
