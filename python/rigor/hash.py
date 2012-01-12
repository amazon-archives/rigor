""" Common functions for hashing files """

import hashlib

def hash(path):
	""" Returns a SHA-1 hash of a path """
	sha1 = hashlib.sha1()
	if hasattr(path, 'read'):
		f = path
	else:
		f = open(path, 'rb')
	while True:
		buf = f.read(0x100000)
		if not buf:
			break
		sha1.update(buf)
	return sha1.hexdigest()
