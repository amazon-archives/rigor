""""
Script to delete ground truth (image, thumbnail, and all!)
"""
import argparse
import rigor.imageops
from rigor.dbmapper import DatabaseMapper
from rigor.database import Database

parser = argparse.ArgumentParser(description='Deletes ground truth (image, thumbnail, and all!)')
parser.add_argument('database', help='Name of database to use')
parser.add_argument('delete_ids', metavar='delete_id', nargs='+', type=int, help='ID(s) of images to delete')
args = parser.parse_args()
db = Database(args.database)
db_mapper = DatabaseMapper(db)
for image_id in args.delete_ids:
	image = db_mapper.get_image_by_id(image_id)
	print("OBLITERATING {}".format(image['id']))
	rigor.imageops.destroy_image(db, image)
