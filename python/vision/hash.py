""" Common functions for hashing files """

import hashlib

def hash(path):
	""" Returns a SHA-1 hash of a path """
	sha1 = hashlib.sha1()
	with open(path, 'rb') as f:
		while True:
			buf = f.read(0x100000)
			if not buf:
				break
			sha1.update(buf)
	return sha1.hexdigest()
