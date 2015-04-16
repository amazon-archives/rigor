"""Add percept data file size

Revision ID: 3c0336c4339d
Revises: 530c9dcd36a1
Create Date: 2015-04-06 15:30:35.348191

"""

# revision identifiers, used by Alembic.
revision = '3c0336c4339d'
down_revision = '530c9dcd36a1'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
	op.add_column('percept', sa.Column('byte_count', sa.Integer))

def downgrade():
	op.drop_column('percept', 'byte_count')
