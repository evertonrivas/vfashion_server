from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id       = sa.Column("id",sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    username = sa.Column("username",sa.String(100), nullable=False)
    password = sa.Column(sa.String(255), nullable=False)
    name     = sa.Column(sa.String(255), nullable=False)
    type     = sa.Column(sa.CHAR(1),nullable=False,default='L',comment='A = Administrador, L = Lojista, R = Representante')

class Product(db.Model):
    __tablename__ = "products"
    id       = sa.Column("id",sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    prodCode = sa.Column("prodCode",sa.String(50),nullable=False)
    barCode  = sa.Column("barCode",sa.String(128))
    refCode  = sa.Column("refCode",sa.String(50),nullable=False)
    name     = sa.Column("name",sa.String(255),nullable=False)
    description = sa.Column("description",sa.String(255))
    observation = sa.Column("objservation",sa.Text)
    ncm         = sa.Column("ncm",sa.String(50))
    image       = sa.Column("image",sa.String(500))
    price       = sa.Column("price",sa.Float,nullable=False)
    price_pdv   = sa.Column("price_pdv",sa.Float,nullable=True)
    measure_unit = sa.Column("measure_unit",sa.CHAR(2),nullable=False)
    structure    = sa.Column("structure",sa.CHAR(1),nullable=False,default='S',comment="S = Simples, C = Composto")

class ProductSku(db.Model):
    __tablename__ = "products_sku"
    id_product = sa.Column("id_product",sa.Integer,primary_key=True,nullable=False)
    color      = sa.Column("color",sa.String(10),primary_key=True,nullable=False)
    size       = sa.Column("size",sa.String(5),primary_key=True,nullable=False)
    quantity   = sa.Column("quantity",sa.Integer)


class Customer(db.Model):
    __tablename__ = "customers"
    id = sa.Column("id",sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name = sa.Column("name",sa.String(255),nullable=False)
    taxvat = sa.Column("taxvat",sa.String(30),nullable=False)
    state_region = sa.Column("state_region",sa.CHAR(2),nullable=False)
    city = sa.Column("city",sa.String(100),nullable=False)
    neighborhood = sa.Column("neighborhood",sa.String(150),nullable=False)
    phone = sa.Column("phone",sa.String(30),nullable=False)
    email = sa.Column("email",sa.String(150),nullable=False)