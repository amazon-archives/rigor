import constants
import rigor.lockfile
import os.path
import pytest

def test_lockfile_created():
	assert not os.path.exists(constants.kLockFile)
	with rigor.lockfile.LockFile(constants.kLockFile) as lock:
		assert os.path.exists(constants.kLockFile)
	assert not os.path.exists(constants.kLockFile)

def test_lockfile_reentrant():
	lock = rigor.lockfile.LockFile(constants.kLockFile)
	lock.acquire()
	assert os.path.exists(constants.kLockFile)
	lock.acquire()
	assert os.path.exists(constants.kLockFile)
	lock.release()
	assert not os.path.exists(constants.kLockFile)

def test_lockfile_multiple():
	lock_1 = rigor.lockfile.LockFile(constants.kLockFile)
	lock_2 = rigor.lockfile.LockFile(constants.kLockFile)
	lock_1.acquire()
	assert os.path.exists(constants.kLockFile)
	lock_1.acquire()
	with pytest.raises(OSError) as error:
		lock_2.acquire()
	lock_1.release()
	assert not os.path.exists(constants.kLockFile)
