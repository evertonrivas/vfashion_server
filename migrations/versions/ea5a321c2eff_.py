"""empty message

Revision ID: ea5a321c2eff
Revises: b88aa91d350b
Create Date: 2023-03-27 15:23:03.722079

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'ea5a321c2eff'
down_revision = 'b88aa91d350b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cmm_products_categories',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('id_parent', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('date_updated', sa.DateTime(), nullable=True),
    sa.Column('trash', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cmm_products_images',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('id_product', sa.Integer(), nullable=False),
    sa.Column('img_url', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cmm_products_models',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('date_created', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('date_updated', sa.DateTime(), nullable=True),
    sa.Column('trash', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cmm_products_types',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('date_created', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('date_updated', sa.DateTime(), nullable=True),
    sa.Column('trash', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('cmm_products_model')
    op.drop_table('cmm_products_image')
    op.drop_table('cmm_products_category')
    op.drop_table('cmm_products_type')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cmm_products_type',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=128), nullable=False),
    sa.Column('date_created', mysql.DATETIME(), server_default=sa.text('current_timestamp()'), nullable=False),
    sa.Column('date_updated', mysql.DATETIME(), nullable=True),
    sa.Column('trash', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('cmm_products_category',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=128), nullable=False),
    sa.Column('date_created', mysql.DATETIME(), server_default=sa.text('current_timestamp()'), nullable=False),
    sa.Column('date_updated', mysql.DATETIME(), nullable=True),
    sa.Column('trash', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('id_parent', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('cmm_products_image',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('id_product', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('img_url', mysql.VARCHAR(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('cmm_products_model',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('date_created', mysql.DATETIME(), server_default=sa.text('current_timestamp()'), nullable=False),
    sa.Column('date_updated', mysql.DATETIME(), nullable=True),
    sa.Column('trash', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.drop_table('cmm_products_types')
    op.drop_table('cmm_products_models')
    op.drop_table('cmm_products_images')
    op.drop_table('cmm_products_categories')
    # ### end Alembic commands ###
