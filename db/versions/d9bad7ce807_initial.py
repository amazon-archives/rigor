"""initial

Revision ID: d9bad7ce807
Revises: 
Create Date: 2015-01-06 11:18:05.638754

"""

# revision identifiers, used by Alembic.
revision = 'd9bad7ce807'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
from rigor.types import Point, Polygon
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence, DropSequence
from datetime import datetime


def upgrade():
	percept_id_seq = Sequence('percept_id_seq')
	op.create_table(
			'percept',
			sa.Column('id', sa.Integer, percept_id_seq, primary_key=True),
			sa.Column('locator', sa.Text, unique=True, nullable=False),
			sa.Column('hash', sa.Text),
			sa.Column('stamp', sa.DateTime(timezone=True)),
			sa.Column('x_size', sa.Integer),
			sa.Column('y_size', sa.Integer),
			sa.Column('format', sa.Text, nullable=False),
			sa.Column('device_id', sa.Text),
			sa.Column('sample_count', sa.BigInteger),
			sa.Column('sample_rate', sa.Float(precision=53))
	)
	create_sequence(percept_id_seq)

	provider = sa.Enum('gps', 'network', name='provider')
	#provider.create(op.get_bind(), checkfirst=True)

	op.create_table(
			'percept_sensors',
			sa.Column('percept_id', sa.Integer, sa.ForeignKey('percept.id'), primary_key=True),
			sa.Column('location', Point),
			sa.Column('location_accuracy', sa.Float),
			sa.Column('location_provider', provider),
			sa.Column('bearing', sa.Float),
			sa.Column('bearing_accuracy', sa.Float),
			sa.Column('altitude', sa.Float),
			sa.Column('altitude_accuracy', sa.Float),
			sa.Column('speed', sa.Float),
			sa.Column('acceleration_x', sa.Float(precision=53)),
			sa.Column('acceleration_y', sa.Float(precision=53)),
			sa.Column('acceleration_z', sa.Float(precision=53))
	)

	annotation_id_seq = Sequence('annotation_id_seq')
	op.create_table(
			'annotation',
			sa.Column('id', sa.Integer,annotation_id_seq, primary_key=True),
			sa.Column('percept_id', sa.Integer, sa.ForeignKey('percept.id'), nullable=False),
			sa.Column('confidence', sa.SmallInteger, nullable=False),
			sa.Column('stamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
			sa.Column('boundary', Polygon),
			sa.Column('domain', sa.Text, nullable=False),
			sa.Column('model', sa.Text)
	)
	create_sequence(annotation_id_seq)

	op.create_table(
			'percept_tag',
			sa.Column('percept_id', sa.Integer, sa.ForeignKey('percept.id'), primary_key=True),
			sa.Column('name', sa.Text, primary_key=True),
	)

	op.create_table(
			'annotation_tag',
			sa.Column('annotation_id', sa.Integer, sa.ForeignKey('annotation.id'), primary_key=True),
			sa.Column('name', sa.Text, primary_key=True)
	)

	op.create_table(
			'percept_property',
			sa.Column('percept_id', sa.Integer, sa.ForeignKey('percept.id'), primary_key=True),
			sa.Column('name', sa.Text, primary_key=True),
			sa.Column('value', sa.Text)
	)

	op.create_table(
			'annotation_property',
			sa.Column('annotation_id', sa.Integer, sa.ForeignKey('annotation.id'), primary_key=True),
			sa.Column('name', sa.Text, primary_key=True),
			sa.Column('value', sa.Text)
	)

	collection_id_seq = Sequence('collection_id_seq')
	op.create_table(
			'collection',
			sa.Column('id', sa.Integer, collection_id_seq, primary_key=True),
			sa.Column('name', sa.Text),
			sa.Column('source', sa.Text)
	)
	create_sequence(collection_id_seq)

	op.create_table(
			'percept_collection',
			sa.Column('percept_id', sa.Integer, sa.ForeignKey('percept.id'), primary_key=True),
			sa.Column('collection_id', sa.Integer, sa.ForeignKey('collection.id'), primary_key=True),
			sa.Column('collection_n', sa.Integer)
	)

	meta = op.create_table(
			'meta',
			sa.Column('key', sa.Text, primary_key=True),
			sa.Column('value', sa.Text)
	)

	op.bulk_insert(meta, [{ 'key': 'repository_root', 'value': 'UNSET' }], multiinsert=False)

def downgrade():
	op.drop_table('meta')
	op.drop_table('annotation_tag')
	op.drop_table('annotation_property')
	op.drop_table('annotation')
	op.drop_table('percept_collection')
	op.drop_table('collection')
	op.drop_table('percept_tag')
	op.drop_table('percept_property')
	op.drop_table('percept_sensors')
	op.drop_table('percept')
	drop_sequence(Sequence('percept_id_seq'))
	drop_sequence(Sequence('annotation_id_seq'))
	drop_sequence(Sequence('collecton_id_seq'))

def create_sequence(sequence):
	if dialect_supports_sequences():
		op.execute(CreateSequence(sequence))

def drop_sequence(sequence):
	if dialect_supports_sequences():
		op.execute(DropSequence(sequence))

def dialect_supports_sequences():
	return op._proxy.migration_context.dialect.supports_sequences
