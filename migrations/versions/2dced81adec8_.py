"""empty message

Revision ID: 2dced81adec8
Revises: ab212e9daa9e
Create Date: 2023-03-17 13:58:24.864855

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '2dced81adec8'
down_revision = 'ab212e9daa9e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cmm_products_image',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_product', sa.Integer(), nullable=False),
    sa.Column('img_url', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('cmm_product_image')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cmm_product_image',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('id_product', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('img_url', mysql.VARCHAR(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.drop_table('cmm_products_image')
    # ### end Alembic commands ###