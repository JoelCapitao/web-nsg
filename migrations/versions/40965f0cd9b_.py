"""empty message

Revision ID: 40965f0cd9b
Revises: 5175173f40f
Create Date: 2015-12-22 14:52:41.726523

"""

# revision identifiers, used by Alembic.
revision = '40965f0cd9b'
down_revision = '5175173f40f'

from alembic import op
from sqlalchemy import Column, String



def upgrade():
    op.drop_column('project_versioning', 'fillingRatio')
    op.add_column('project_versioning',
                  Column('fillingRatio', String)
                  )


def downgrade():
    pass
