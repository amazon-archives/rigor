"""Support multiple repositories

Revision ID: 530c9dcd36a1
Revises: d9bad7ce807
Create Date: 2015-03-10 15:55:33.305777

"""

# revision identifiers, used by Alembic.
revision = '530c9dcd36a1'
down_revision = 'd9bad7ce807'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
	op.add_column('percept', sa.Column('credentials', sa.Text))
	meta = table('meta', column('key', sa.Text))
	op.execute(meta.delete().where(meta.c.key == op.inline_literal('repository_root')))

def downgrade():
	op.drop_column('percept', 'credentials')
	op.bulk_insert(meta, [{ 'key': 'repository_root', 'value': 'UNSET' }], multiinsert=False)
