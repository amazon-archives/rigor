""" Common functions for hashing files """

import hashlib

def sha1_hash(path):
	""" Returns a SHA-1 hash of a path """
	sha1 = hashlib.sha1()
	if hasattr(path, 'read'):
		file_object = path
	else:
		file_object = open(path, 'rb')
	while True:
		buf = file_object.read(0x100000)
		if not buf:
			break
		sha1.update(buf)
	return sha1.hexdigest()
