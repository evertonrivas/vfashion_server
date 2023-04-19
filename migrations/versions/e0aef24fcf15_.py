"""empty message

Revision ID: e0aef24fcf15
Revises: 28185cef191d
Create Date: 2023-04-17 16:58:54.465731

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e0aef24fcf15'
down_revision = '28185cef191d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('b2b_orders', schema=None) as batch_op:
        batch_op.alter_column('total_itens',
               existing_type=mysql.DECIMAL(precision=10, scale=2),
               type_=sa.Integer(),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('b2b_orders', schema=None) as batch_op:
        batch_op.alter_column('total_itens',
               existing_type=sa.Integer(),
               type_=mysql.DECIMAL(precision=10, scale=2),
               existing_nullable=False)

    # ### end Alembic commands ###