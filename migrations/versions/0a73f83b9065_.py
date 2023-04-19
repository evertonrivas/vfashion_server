"""empty message

Revision ID: 0a73f83b9065
Revises: 3f8d24d9f054
Create Date: 2023-04-17 14:16:52.538836

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a73f83b9065'
down_revision = '3f8d24d9f054'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('b2b_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('track_code', sa.String(length=30), nullable=True, comment='Código de rastreamento'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('b2b_orders', schema=None) as batch_op:
        batch_op.drop_column('track_code')

    # ### end Alembic commands ###