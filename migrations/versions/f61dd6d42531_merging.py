"""merging

Revision ID: f61dd6d42531
Revises: 080cfe1b4221, 4c11c6800e85, 655c694c1008, 68f9dfb529f0, af2361c3785a
Create Date: 2023-02-23 22:06:44.229150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f61dd6d42531'
down_revision = ('080cfe1b4221', '4c11c6800e85', '655c694c1008', '68f9dfb529f0', 'af2361c3785a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
