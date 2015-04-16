import pytest
import db
from rigor.types import Meta

@pytest.fixture
def testdb():
	return db.get_database()

def test_session_commit(testdb):
	with testdb.get_session() as session:
		meta = Meta('test_key', 'test_value')
		session.add(meta)
		session.commit()
	with testdb.get_session() as session:
		meta = session.query(Meta).get('test_key')
		assert meta.value == 'test_value'

def test_session_rollback(testdb):
	with testdb.get_session() as session:
		meta = Meta('test_key', 'test_value')
		session.add(meta)
		session.rollback()
	with testdb.get_session() as session:
		meta = session.query(Meta).get('test_key')
		assert meta is None

def test_session_context_commit(testdb):
	with testdb.get_session() as session:
		meta = Meta('test_key', 'test_value')
		session.add(meta)
	with testdb.get_session() as session:
		meta = session.query(Meta).get('test_key')
		assert meta.value == 'test_value'

def test_session_context_rollback(testdb):
	with testdb.get_session(False) as session:
		meta = Meta('test_key', 'test_value')
		session.add(meta)
	with testdb.get_session() as session:
		meta = session.query(Meta).get('test_key')
		assert meta is None
