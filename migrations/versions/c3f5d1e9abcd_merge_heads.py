"""Merge heads a920b94c9298 and b4c2d9f0e5e1

Revision ID: c3f5d1e9abcd
Revises: a920b94c9298, b4c2d9f0e5e1
Create Date: 2025-08-31 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f5d1e9abcd'
down_revision = ('a920b94c9298', 'b4c2d9f0e5e1')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge revision to resolve multiple heads. No DB operations.
    pass


def downgrade():
    pass
