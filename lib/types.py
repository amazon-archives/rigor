""" Database-backed objects in Rigor """

import sqlalchemy as sa
from sqlalchemy.ext.declarative import as_declarative
from rigor.database import kNamingConvention
import rigor.utils
import ast

kMetaData = sa.MetaData(naming_convention=kNamingConvention)

@as_declarative(metadata=kMetaData)
class RigorBase(object):
	""" SQLAlchemy declarative base with some serialization helpers built in """

	def serialize(self, force_load=False, seen=None):
		"""
		Returns a representation of this object (and possibly all children) as a :py:class:`dict`.

		:param bool force_load: if :py:const:`False`, only fields that have already been loaded from the database are included. If :py:const:`True`, then all fields will be fetched and serialized.
		:param set seen: Used for recursive calls, this is a set of object names that have already been serialized at a higher lever. This helps prevent infinite recursion. It shouldn't need to be used manually.
		"""
		if seen is None:
			seen = set()
		else:
			seen = set(seen)

		result = dict()
		seen.add(self.__tablename__)
		mapper = sa.orm.class_mapper(self.__class__)
		state = sa.inspect(self)
		for column in mapper.columns:
			value = getattr(self, column.key)
			result[column.key] = value
		for name, relationship in mapper.relationships.items():
			if relationship.target.name in seen:
				continue
			if not force_load and name in state.unloaded:
				continue
			seen.add(relationship.target.name)
			other = getattr(self, name)
			if other is None:
				continue
			if isinstance(other, sa.orm.collections.MappedCollection):
				result[name] = dict([value.serialize(force_load, seen).items()[0] for value in other.values()])
			elif relationship.uselist:
				result[name] = [value.serialize(force_load, seen) for value in other]
			else:
				result[name] = other.serialize(force_load, seen)
		return result

	def __getstate__(self):
		return self.serialize(force_load=True)

	@classmethod
	def deserialize(cls, obj, seen=None, result=None):
		if seen is None:
			seen = set()
		else:
			seen = set(seen)

		if result is None:
			result = cls()
		seen.add(result.__tablename__)
		mapper = sa.orm.class_mapper(cls)
		for column in mapper.columns:
			if column.key in obj:
				setattr(result, column.key, obj[column.key])
		for name, relationship in mapper.relationships.items():
			if relationship.target.name in seen:
				continue
			seen.add(relationship.target.name)
			if not name in obj:
				continue
			collection = getattr(result, name)
			other_cls = relationship.argument()
			values = obj[name]
			if relationship.collection_class and isinstance(relationship.collection_class(), sa.orm.collections.MappedCollection):
				for key, value in values.iteritems():
					collection[key] = other_cls.deserialize({key: value}, seen)
			elif relationship.uselist:
				for value in values:
					collection.append(other_cls.deserialize(value, seen))
			else:
				setattr(result, name, other_cls.deserialize(values, seen))
		return result

	def __setstate__(self, state):
		self.__init__()
		return self.deserialize(state, result=self)

	def __setattr__(self, name, value):
		if name == 'stamp':
			value = rigor.utils.parse_timestamp(value)
		object.__setattr__(self, name, value)

class ThreeDimensionalArray(object):
	"""
	A composite data type representing a 3-dimensional array

	:param x: X-axis value
	:param y: Y-axis value
	:param z: Z-axis value
	"""
	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z

	def serialize(self):
		return self.__composite_values__()

	@classmethod
	def deserialize(cls, obj):
		return cls(*obj)

	def __composite_values__(self):
		return self.x, self.y, self.z

	def __repr__(self):
		return "ThreeDimensionalArray(x={0}, y={1}, z={2})".format(self.x, self.y, self.z)

	def __eq__(self, other):
		return isinstance(other, ThreeDimensionalArray) and other.x == self.x and other.y == self.y and other.z == self.z

	def __ne__(self, other):
		return not self.__eq__(other)

class Point(sa.types.UserDefinedType):
	""" Type representing a 2D geometric point """

	def get_col_spec(self):
		return "POINT"

	def bind_processor(self, dialect):
		def process(value):
			if value is None:
				return None
			return '({0:n}, {1:n})'.format(value[0], value[1])
		return process

	def result_processor(self, dialect, coltype):
		def process(value):
			if value is None:
				return value
			return ast.literal_eval(value)
		return process

	def python_type(self):
		return tuple

class Polygon(sa.types.UserDefinedType):
	""" Type representing a polygon made up of 2D points """

	def get_col_spec(self):
		return "POLYGON"

	def bind_processor(self, dialect):
		def process(value):
			if value is None:
				return None
			return ', '.join('({0:n}, {1:n})'.format(val[0], val[1]) for val in value)
		return process

	def result_processor(self, dialect, coltype):
		def process(value):
			if value is None:
				return value
			return ast.literal_eval(value)
		return process

	def python_type(self):
		return tuple

class Collection(RigorBase):
	""" A set of items (currently, just percepts) that are related somehow """
	__tablename__ = 'collection'
	id = sa.Column(sa.Integer, sa.Sequence('collection_id_seq'), primary_key=True)
	name = sa.Column(sa.Text)
	source = sa.Column(sa.Text)

class PerceptCollection(RigorBase):
	""" Relates percepts to collections """
	__tablename__ = 'percept_collection'
	percept_id = sa.Column(sa.Integer, sa.ForeignKey('percept.id'), primary_key=True)
	collection_id = sa.Column(sa.Integer, sa.ForeignKey('collection.id'), primary_key=True)
	collection_n = sa.Column(sa.Integer)
	collection = sa.orm.relationship(lambda: Collection, backref='percept_collection', cascade='all')

class Percept(RigorBase):
	"""
	Represents metadata for a single piece of data that can be annotated, providing a ground truth record, and then passed to an algorithm for processing
	"""
	__tablename__ = 'percept'
	id = sa.Column(sa.Integer, sa.Sequence('percept_id_seq'), primary_key=True)
	locator = sa.Column(sa.Text, unique=True, nullable=False)
	credentials = sa.Column(sa.Text)
	hash = sa.Column(sa.Text)
	byte_count = sa.Column(sa.Integer)
	stamp = sa.Column(sa.DateTime(timezone=True))
	x_size = sa.Column(sa.Integer)
	y_size = sa.Column(sa.Integer)
	format = sa.Column(sa.Text, nullable=False)
	device_id = sa.Column(sa.Text)
	sample_count = sa.Column(sa.BigInteger)
	sample_rate = sa.Column(sa.Float(precision=53))
	sensors = sa.orm.relationship(lambda: PerceptSensors, uselist=False, backref='percept', cascade='all, delete-orphan', lazy='joined')
	tags = sa.orm.relationship(lambda: PerceptTag, order_by=lambda: PerceptTag.name, cascade='all, delete-orphan')
	properties = sa.orm.relationship(lambda: PerceptProperty, order_by=lambda: PerceptProperty.name, collection_class=sa.orm.collections.attribute_mapped_collection('name'), cascade='all, delete-orphan')
	annotations = sa.orm.relationship(lambda: Annotation, order_by=lambda: Annotation.id, cascade='all, delete-orphan')
	collections = sa.orm.relationship(lambda: PerceptCollection, backref='percepts', cascade='all')

class PerceptSensors(RigorBase):
	""" Sensor metadata for a :py:class:`Percept` """
	__tablename__ = 'percept_sensors'
	percept_id = sa.Column(sa.Integer, sa.ForeignKey('percept.id'), primary_key=True)
	location = sa.Column(Point)
	location_accuracy = sa.Column(sa.Float)
	location_provider = sa.Column(sa.Enum('gps', 'network', name='provider'))
	bearing = sa.Column(sa.Float)
	bearing_accuracy = sa.Column(sa.Float)
	altitude = sa.Column(sa.Float)
	altitude_accuracy = sa.Column(sa.Float)
	speed = sa.Column(sa.Float)
	acceleration_x = sa.Column(sa.Float(precision=53))
	acceleration_y = sa.Column(sa.Float(precision=53))
	acceleration_z = sa.Column(sa.Float(precision=53))
	acceleration = sa.orm.composite(ThreeDimensionalArray, acceleration_x, acceleration_y, acceleration_z)

class Annotation(RigorBase):
	""" Ground truth annotation for a single percept """
	__tablename__ = 'annotation'
	id = sa.Column(sa.Integer, sa.Sequence('annotation_id_seq'), primary_key=True)
	percept_id = sa.Column(sa.Integer, sa.ForeignKey('percept.id'), nullable=False)
	confidence = sa.Column(sa.SmallInteger, nullable=False)
	stamp = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
	boundary = sa.Column(Polygon)
	domain = sa.Column(sa.Text, nullable=False)
	model = sa.Column(sa.Text)
	tags = sa.orm.relationship(lambda: AnnotationTag, order_by=lambda: AnnotationTag.name, cascade='all, delete-orphan')
	properties = sa.orm.relationship(lambda: AnnotationProperty, order_by=lambda: AnnotationProperty.name, collection_class=sa.orm.collections.attribute_mapped_collection('name'), cascade='all, delete-orphan')

class RigorTag(object):
	""" Mixin for a tag type """
	def serialize(self, _force_load=False, _seen=None):
		return self.name

	@classmethod
	def deserialize(cls, obj, _=None):
		return cls(obj)

class PerceptTag(RigorTag, RigorBase):
	""" A tag that can be used for filtering or describing percepts """
	__tablename__ = 'percept_tag'
	percept_id = sa.Column(sa.Integer, sa.ForeignKey('percept.id'), primary_key=True)
	name = sa.Column(sa.Text, primary_key=True)

	def __init__(self, name=None):
		self.name = name

class AnnotationTag(RigorTag, RigorBase):
	""" A tag that can be used for filtering or describing annotations """
	__tablename__ = 'annotation_tag'
	annotation_id = sa.Column(sa.Integer, sa.ForeignKey('annotation.id'), primary_key=True)
	name = sa.Column(sa.Text, primary_key=True)

	def __init__(self, name=None):
		self.name = name

class RigorProperty(object):
	""" Mixin for a property type """

	def serialize(self, _force_load=False, _serialize=None):
		return {self.name: self.value}

	@classmethod
	def deserialize(cls, obj, _=None):
		unpacked = obj.items()[0]
		return cls(*unpacked)

class PerceptProperty(RigorProperty, RigorBase):
	""" A key and optional value that can be used for filtering or describing percepts """
	__tablename__ = 'percept_property'
	percept_id = sa.Column(sa.Integer, sa.ForeignKey('percept.id'), primary_key=True)
	name = sa.Column(sa.Text, primary_key=True)
	value = sa.Column(sa.Text)

	def __init__(self, name=None, value=None):
		self.name = name
		self.value = value

class AnnotationProperty(RigorProperty, RigorBase):
	""" A key and optional value that can be used for filtering or describing annotations """
	__tablename__ = 'annotation_property'
	annotation_id = sa.Column(sa.Integer, sa.ForeignKey('annotation.id'), primary_key=True)
	name = sa.Column(sa.Text, primary_key=True)
	value = sa.Column(sa.Text)

	def __init__(self, name=None, value=None):
		self.name = name
		self.value = value

class Meta(RigorBase):
	""" Metadata describing an individual Rigor database """
	__tablename__ = 'meta'
	key = sa.Column(sa.Text, primary_key=True)
	value = sa.Column(sa.Text)

	def __init__(self, key=None, value=None):
		self.key = key
		self.value = value
