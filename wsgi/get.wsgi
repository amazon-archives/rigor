""" Fetches an image by its id """

import rigor.database
import rigor.imageops

from rigor.dbmapper import DatabaseMapper, image_mapper

from webob import Request, Response
from webob.exc import HTTPTemporaryRedirect, HTTPNotFound

import sys
import os.path
import urlparse
import urllib

from datetime import datetime

kImageBaseUrl = '/rigor/images'

gDatabase = rigor.database.Database()
gDbMapper = DatabaseMapper(gDatabase)

def get_image(image_id):
	sql = "SELECT * FROM image WHERE id = %s;"
	cursor = gDatabase.get_cursor()
	try:
		cursor.execute(sql, (image_id, ))
		image = cursor.fetch_one(image_mapper)
	finally:
		gDatabase.rollback(cursor)
	return image

def application(environ, start_response):
	image_id = None

	req = Request(environ)

	image_id = int(req.path_info_peek())
	image = get_image(image_id)
	if image is None:
		res = HTTPNotFound()
	else:
		image_path = "/".join((kImageBaseUrl, image['locator'][0:2], image['locator'][2:4], ".".join((image['locator'], image['format']))))
		res = HTTPTemporaryRedirect(location=image_path)
	return res(environ, start_response)
