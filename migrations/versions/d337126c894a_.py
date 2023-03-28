"""empty message

Revision ID: d337126c894a
Revises: 82ad47481343
Create Date: 2023-03-27 22:39:24.052435

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd337126c894a'
down_revision = '82ad47481343'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('b2b_product_stock',
    sa.Column('id_product', sa.Integer(), nullable=False),
    sa.Column('color', sa.String(length=10), nullable=False),
    sa.Column('size', sa.String(length=5), nullable=False),
    sa.Column('quantity', sa.SmallInteger(), nullable=True),
    sa.Column('limited', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id_product', 'color', 'size')
    )
    with op.batch_alter_table('b2b_table_price_product', schema=None) as batch_op:
        batch_op.drop_column('size')
        batch_op.drop_column('color')
        batch_op.drop_column('stock_quantity')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('b2b_table_price_product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stock_quantity', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('color', mysql.VARCHAR(length=10), nullable=False))
        batch_op.add_column(sa.Column('size', mysql.VARCHAR(length=5), nullable=False))

    op.drop_table('b2b_product_stock')
    # ### end Alembic commands ###
