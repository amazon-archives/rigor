import rigor.hash
import os.path
import constants
import io

def test_hash_fileobj():
	data = io.BytesIO('a test string to hash')
	expected = '1f9ea24f2e0b6707fdeb7ea29613b080d8657d5d2dfefbe8130e9c40cf6d9e2d'
	hashed = rigor.hash.sha256_hash(data)
	assert hashed == expected

def test_hash_path():
	data = os.path.join(constants.kExampleImageFile)
	expected = '6ecd86bbe85e03ee2a03eb61ad080fcefe399df1c802fecc79d20949c8986115'
	hashed = rigor.hash.sha256_hash(data)
	assert hashed == expected
