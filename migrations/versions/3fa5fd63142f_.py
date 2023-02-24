"""empty message

Revision ID: 3fa5fd63142f
Revises: 131d0fd3f3c3
Create Date: 2023-02-23 23:08:06.079135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3fa5fd63142f'
down_revision = '131d0fd3f3c3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('crm_funnel_stage', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_funnel', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('crm_funnel_stage', schema=None) as batch_op:
        batch_op.drop_column('id_funnel')

    # ### end Alembic commands ###