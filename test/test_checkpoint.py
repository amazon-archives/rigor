import rigor.checkpoint
import os
import constants
import tempfile
import pytest
import time

def test_checkpointer_empty():
	checkpointer = rigor.checkpoint.Checkpointer(None)
	filename = checkpointer.filename
	with checkpointer:
		assert os.path.exists(filename)
	assert not os.path.exists(filename)

def test_checkpointer_open_file():
	with tempfile.TemporaryFile(prefix='rigor-test-') as test_file:
		checkpointer = rigor.checkpoint.Checkpointer(None, test_file)

def test_checkpointer_remove_on_success():
	checkpointer = rigor.checkpoint.Checkpointer(None)
	filename = checkpointer.filename
	with checkpointer:
		assert os.path.exists(filename)
	assert not os.path.exists(filename)

def test_checkpointer_keep_after_error():
	checkpointer = rigor.checkpoint.Checkpointer(None)
	filename = checkpointer.filename
	with pytest.raises(StandardError):
		with checkpointer:
			assert os.path.exists(filename)
			raise StandardError
	assert os.path.exists(filename)
	os.unlink(filename)
	assert not os.path.exists(filename)

def test_checkpointer_keep():
	checkpointer = rigor.checkpoint.Checkpointer(None, delete_on_success=False)
	filename = checkpointer.filename
	with checkpointer:
		assert os.path.exists(filename)
	assert os.path.exists(filename)
	os.unlink(filename)
	assert not os.path.exists(filename)

@pytest.mark.parametrize('flush', [(True, ), (False, )])
def test_checkpointer_store(flush):
	checkpointer = rigor.checkpoint.Checkpointer(None, delete_on_success=False)
	filename = checkpointer.filename
	test_id = 23232
	test_entry = ('a', 'b', 1, 2, {'c': 4})
	with checkpointer:
		checkpointer.log(test_id, test_entry, flush)
	with open(filename, 'rb') as old_file:
		checkpointer, checkpoint = rigor.checkpoint.Checkpointer.resume(old_file)
		assert test_id in checkpoint.seen
		assert test_entry == checkpoint.results[0]
	os.unlink(filename)

def test_checkpointer_parameters():
	start = time.time()
	parameters = constants.kExamplePercept
	checkpointer = rigor.checkpoint.Checkpointer(parameters, delete_on_success=False)
	filename = checkpointer.filename
	checkpointer.close(True)
	with open(filename, 'rb') as checkpoint_file:
		timestamp, read_parameters = rigor.checkpoint.Checkpointer.read_header(checkpoint_file)
	assert timestamp > start
	assert timestamp < time.time()
	assert read_parameters == parameters
	os.unlink(filename)
