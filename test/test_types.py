import pytest
import datetime
import rigor.types
import db
import constants
import cPickle as pickle

@pytest.fixture
def typesdb():
	return db.get_database()

def test_percept_count(typesdb):
	with typesdb.get_session() as session:
		query = session.query(rigor.types.Percept)
		assert query.count() == 12

def test_add_percept(typesdb):
	locator = constants.kExamplePercept['locator']
	x_size = 30
	y_size = 20
	format = 'raw'
	device_id = '1234axxrd'
	location = (23, 44)
	percept_id = None
	with typesdb.get_session() as session:
		percept = rigor.types.Percept()
		percept.locator = locator
		percept.x_size = x_size
		percept.y_size = y_size
		percept.format = format
		percept.device_id = device_id
		percept.sensors = rigor.types.PerceptSensors()
		percept.sensors.location = location
		session.add(percept)
		session.flush()
		percept_id = percept.id

	with typesdb.get_session() as session:
		fetched = session.query(rigor.types.Percept).get(percept_id)
		assert fetched.locator == locator
		assert fetched.x_size == x_size
		assert fetched.y_size == y_size
		assert fetched.format == format
		assert fetched.device_id == device_id
		assert fetched.sensors.location == location

def test_get_percept_tags(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(780034)
		assert len(percept.tags) == 3
		assert 'simple' in [tag.name for tag in percept.tags]

def test_add_percept_tag(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(642924)
		percept.tags.append(rigor.types.PerceptTag('bumblebee'))

	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(642924)
		assert len(percept.tags) == 4
		assert 'bumblebee' in [tag.name for tag in percept.tags]

def test_add_percept_tag_exception(typesdb):
	with pytest.raises(StandardError) as exception_info:
		with typesdb.get_session() as session:
			percept = session.query(rigor.types.Percept).get(642924)
			percept.tags.append(rigor.types.PerceptTag('bumblebee'))
			raise StandardError("Test failure")

	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(642924)
		assert len(percept.tags) == 3
		assert 'bumblebee' not in [tag.name for tag in percept.tags]

def test_add_percept_tag_rollback(typesdb):
	with typesdb.get_session(False) as session:
		percept = session.query(rigor.types.Percept).get(642924)
		percept.tags.append(rigor.types.PerceptTag('bumblebee'))

	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(642924)
		assert len(percept.tags) == 3
		assert 'bumblebee' not in [tag.name for tag in percept.tags]

def test_remove_percept_tag(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(585354)
		del percept.tags[1]

	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(585354)
		assert len(percept.tags) == 1
		assert 'train' not in [tag.name for tag in percept.tags]

def test_add_percept_property(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(485447)
		percept.properties['dwelling'] = rigor.types.PerceptProperty(name='dwelling', value='bungalow')

	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(485447)
		assert len(percept.properties) == 2
		assert percept.properties['dwelling'].value == 'bungalow'

def test_remove_percept_property(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(832620)
		del percept.properties['val1']

	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(832620)
		assert len(percept.properties) == 0

def test_remove_percept(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(572232)
		session.delete(percept)

	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(572232)
		assert percept is None

def test_serialize_percept_force_load(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(832620)
		percept = percept.serialize(True)

	assert percept['format'] == constants.kExamplePercept['format']
	assert percept['hash'] == '1ff66afcf0eb4f5ef392fd8e942e0ff2139dda81'
	assert len(percept['annotations']) == len(constants.kExamplePercept['annotations'])
	assert percept['annotations'][0]['confidence'] == constants.kExamplePercept['annotations'][0]['confidence']

def test_serialize_percept_no_force_load(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(572232)
		percept = percept.serialize(False)

	assert percept['format'] == constants.kExamplePercept['format']
	assert percept['hash'] == '3c7e44beccd81dc8b6ee534423e5178cec1390f0'
	assert 'tags' not in percept
	assert 'annotations' not in percept

def test_pickle_unpickle_percept(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(832620)
		pickled = pickle.dumps(percept)
	unpickled = pickle.loads(pickled)
	assert unpickled.format == constants.kExamplePercept['format']
	assert unpickled.hash == '1ff66afcf0eb4f5ef392fd8e942e0ff2139dda81'
	assert len(unpickled.annotations) == len(constants.kExamplePercept['annotations'])
	assert unpickled.annotations[0].confidence == constants.kExamplePercept['annotations'][0]['confidence']

def test_serialize_acceleration(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(832620)
		acceleration = percept.sensors.acceleration
		assert acceleration == rigor.types.ThreeDimensionalArray(0.1, 0.2, 0.3)
		acceleration = acceleration.serialize()
		assert acceleration == (0.1, 0.2, 0.3)

def test_deserialize_acceleration():
	acceleration = (0.1, 0.2, 0.3)
	deserialized = rigor.types.ThreeDimensionalArray.deserialize(acceleration)
	assert deserialized.x == acceleration[0]
	assert deserialized.y == acceleration[1]
	assert deserialized.z == acceleration[2]

def test_acceleration_repr(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(832620)
		acceleration = percept.sensors.acceleration
		assert repr(acceleration) == "ThreeDimensionalArray(x=0.1, y=0.2, z=0.3)"

def test_acceleration_equality():
	first = rigor.types.ThreeDimensionalArray.deserialize((2.8, 3.1, 4.1))
	second = rigor.types.ThreeDimensionalArray.deserialize((2.1, 1.1, 0.1))
	third = rigor.types.ThreeDimensionalArray.deserialize((2.1, 1.1, 0.1))
	assert first != second
	assert second == third

def test_point():
	point = rigor.types.Point()
	bind = point.bind_processor(None)
	result = point.result_processor(None, None)
	assert point.get_col_spec() == "POINT"
	assert bind(None) is None
	assert bind((1, 2)) == '(1, 2)'
	assert result(None) is None
	assert result('(1, 2)') == (1, 2)
	assert point.python_type() is tuple

def test_polygon():
	polygon = rigor.types.Polygon()
	bind = polygon.bind_processor(None)
	result = polygon.result_processor(None, None)
	assert polygon.get_col_spec() == "POLYGON"
	assert bind(None) is None
	assert bind(((1, 2), (3, 4))) == '(1, 2), (3, 4)'
        assert bind(((1.25, 2.5), (3.25, 4))) == '(1.25, 2.5), (3.25, 4)'
	assert result(None) is None
	assert result('((1, 2), (3, 4))') == ((1, 2), (3, 4))
        assert result('((1.25, 2.5), (3.25, 4))') == ((1.25, 2.5), (3.25, 4))
	assert polygon.python_type() is tuple

def test_serialize_percept_tag(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(485447)
		first_tag = percept.tags[0].serialize()
		assert first_tag == 'c'

def test_serialize_percept_property(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(485447)
		first_property = percept.properties.items()[0][1].serialize()
		assert first_property['val1'] == 'val2'

def test_deserialize_percept(typesdb):
	percept = rigor.types.Percept.deserialize(constants.kExamplePercept)
	assert percept.format == constants.kExamplePercept['format']
	assert percept.hash == constants.kExamplePercept['hash']
	assert len(percept.annotations) == len(constants.kExamplePercept['annotations'])
	assert percept.annotations[0].confidence == constants.kExamplePercept['annotations'][0]['confidence']

def test_serialize_percept_multi_annotations_multi_properties(typesdb):
	with typesdb.get_session() as session:
		percept = session.query(rigor.types.Percept).get(832620).serialize(True)
		assert len(percept['annotations']) == 3
		assert percept['annotations'][0]['properties']['prop'] == 'value1'
		assert percept['annotations'][1]['properties']['prop'] == 'value2'
		assert percept['annotations'][2]['properties']['prop'] == 'value3'

def test_deserialize_percept_multi_annotations_multi_properties(typesdb):
	with typesdb.get_session() as session:
		percept_db = session.query(rigor.types.Percept).get(832620)
		percept = rigor.types.Percept.deserialize(percept_db.serialize(True))
		assert len(percept.annotations) == 3
		assert percept.annotations[0].properties['prop'].value == 'value1'
		assert percept.annotations[1].properties['prop'].value == 'value2'
		assert percept.annotations[2].properties['prop'].value == 'value3'
