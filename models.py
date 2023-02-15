from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy import func

db = SQLAlchemy()

class CmmUsers(db.Model):
    id       = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    username = sa.Column(sa.String(100), nullable=False)
    password = sa.Column(sa.String(255), nullable=False)
    name     = sa.Column(sa.String(255), nullable=False)
    type     = sa.Column(sa.CHAR(1),nullable=False,default='L',comment='A = Administrador, L = Lojista, R = Representante')
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())


class CmmProducts(db.Model):
    id       = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    prodCode = sa.Column(sa.String(50),nullable=False)
    barCode  = sa.Column(sa.String(128))
    refCode  = sa.Column(sa.String(50),nullable=False)
    name     = sa.Column(sa.String(255),nullable=False)
    description = sa.Column(sa.String(255))
    observation = sa.Column(sa.Text)
    ncm         = sa.Column(sa.String(50))
    image       = sa.Column(sa.String(500))
    price       = sa.Column(sa.Float,nullable=False)
    price_pdv   = sa.Column(sa.Float,nullable=True)
    measure_unit = sa.Column(sa.CHAR(2),nullable=False)
    structure    = sa.Column(sa.CHAR(1),nullable=False,default='S',comment="S = Simples, C = Composto")
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())


class CmmProductsSku(db.Model):
    id_product = sa.Column(sa.Integer,primary_key=True,nullable=False)
    color      = sa.Column(sa.String(10),primary_key=True,nullable=False)
    size       = sa.Column(sa.String(5),primary_key=True,nullable=False)
    quantity   = sa.Column(sa.Integer)


class CmmCustomers(db.Model):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = sa.Column(sa.String(255),nullable=False)
    taxvat       = sa.Column(sa.String(30),nullable=False,comment="CPF ou CNPJ no Brasil")
    state_region = sa.Column(sa.CHAR(2),nullable=False)
    city         = sa.Column(sa.String(100),nullable=False)
    postal_code  = sa.Column(sa.String(30),nullable=False)
    neighborhood = sa.Column(sa.String(150),nullable=False)
    phone        = sa.Column(sa.String(30),nullable=False)
    email        = sa.Column(sa.String(150),nullable=False)
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())


class CmmCustomersGrupo(db.Model):
    id = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name = sa.Column(sa.String(128),nullable=False)


class B2bOrders(db.Model):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    id_customer  = sa.Column(sa.Integer,nullable=False)
    id_payment_condition = sa.Column(sa.Integer,nullable=False)
    make_online  = sa.Column(sa.Boolean,nullable=False,default=True,comment="Os pedidos do sistema podem ser online ou offline")
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())


class B2bOrdersProducts(db.Model):
    id_order   = sa.Column(sa.Integer,nullable=False,primary_key=True)
    id_product = sa.Column(sa.Integer,nullable=False,primary_key=True)
    quantity   = sa.Column(sa.Integer,nullable=False)


class B2bPaymentConditions(db.Model):
    id            = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name          = sa.Column(sa.String(100),nullable=False)
    received_days = sa.Column(sa.SmallInteger,nullable=False,default=1,comment="Dias para receber o valor")
    installments  = sa.Column(sa.SmallInteger,nullable=False,default=1,comment="Número de parcelas")
    date_created  = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated  = sa.Column(sa.DateTime,onupdate=func.now())


class CrmFunnel(db.Model):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = sa.Column(sa.String(128),nullable=False)
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())


class CrmFunnelStage(db.Model):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = sa.Column(sa.String(128),nullable=False)
    order        = sa.Column(sa.CHAR(2),nullable=False,default='CD',comment='CD = ')
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())


class CrmFunnelStageCustomer(db.Model):
    id_funnel_stage = sa.Column(sa.Integer,primary_key=True,nullable=False)
    id_customer     = sa.Column(sa.Integer,primary_key=True,nullable=False)
    date_created    = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated    = sa.Column(sa.DateTime,onupdate=func.now())