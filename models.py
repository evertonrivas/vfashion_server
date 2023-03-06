from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime,timedelta
import jwt
import bcrypt

db = SQLAlchemy()

class CmmUsers(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    username     = sa.Column(sa.String(100), nullable=False)
    password     = sa.Column(sa.String(255), nullable=False)
    type         = sa.Column(sa.CHAR(1),nullable=False,default='L',comment='A = Administrador, L = Lojista, R = Representante, V = Vendedor, U = User')
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    active       = sa.Column(sa.Boolean,nullable=False,default=True)
    token        = sa.Column(sa.String(255),index=True,unique=True)
    token_expire = sa.Column(sa.DateTime)

    def hash_pwd(self,pwd:str):
        self.password = bcrypt.hashpw(pwd.encode(),bcrypt.gensalt())
    
    def get_token(self,expires_in:int=7200):
        now = datetime.utcnow()
        if self.token and self.token_expire > now + timedelta(seconds=expires_in):
            return self.token

        #encode e decode por causa da diferenca de versoes do windows que pode retornar byte array ao inves de str
        self.token = jwt.encode({"username":str(self.username),"exp": (now + timedelta(seconds=expires_in)) },"VENDA_FASHION").encode().decode()
        self.token_expire = (now + timedelta(seconds=expires_in))
        return self.token

    def revoke_token(self):
        self.token_expire = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = CmmUsers.query.filter(CmmUsers.token==token).first()
        if user is None or user.token_expire < datetime.utcnow():
            return None
        return user


class CmmUserEntity(db.Model,SerializerMixin):
    id_user     = sa.Column(sa.Integer,nullable=False,primary_key=True)
    id_entity   = sa.Column(sa.Integer,nullable=False,primary_key=True,default=0)
    id_consumer = sa.Column(sa.Integer,nullable=False,primary_key=True,default=0)


class CmmCategory(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,primary_key=True,autoincrement=True,nullable=False)
    name         = sa.Column(sa.String(128),nullable=False)
    id_parent    = sa.Column(sa.Integer,nullable=True)
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    trash        = sa.Column(sa.Boolean,nullable=False,default=False)


class CmmProducts(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    id_category  = sa.Column(sa.Integer,nullable=False)
    prodCode     = sa.Column(sa.String(50),nullable=False)
    barCode      = sa.Column(sa.String(128))
    refCode      = sa.Column(sa.String(50),nullable=False)
    name         = sa.Column(sa.String(255),nullable=False)
    description  = sa.Column(sa.String(255))
    observation  = sa.Column(sa.Text)
    ncm          = sa.Column(sa.String(50))
    image        = sa.Column(sa.String(500))
    price        = sa.Column(sa.Float,nullable=False)
    price_pdv    = sa.Column(sa.Float,nullable=True)
    measure_unit = sa.Column(sa.CHAR(2),nullable=False)
    structure    = sa.Column(sa.CHAR(1),nullable=False,default='S',comment="S = Simples, C = Composto")
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    trash        = sa.Column(sa.Boolean,nullable=False,default=False)


class CmmProductType(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,nullable=False,primary_key=True,autoincrement=True)
    name         = sa.Column(sa.String(128),nullable=False)
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    trash        = sa.Column(sa.Boolean,nullable=False,default=False)


class CmmProductModel(db.Model,SerializerMixin):
    id = sa.Column(sa.Integer,nullable=False,primary_key=True,autoincrement=True)
    name = sa.Column(sa.String(255),nullable=False)
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    trash        = sa.Column(sa.Boolean,nullable=False,default=False)


class CmmProductsSku(db.Model,SerializerMixin):
    id_product = sa.Column(sa.Integer,primary_key=True,nullable=False)
    id_type    = sa.Column(sa.Integer,primary_key=True,nullable=False)
    id_model   = sa.Column(sa.Integer,primary_key=True,nullable=False)
    color      = sa.Column(sa.String(10),primary_key=True,nullable=False)
    size       = sa.Column(sa.String(5),primary_key=True,nullable=False)


class CmmProductsGrid(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,primary_key=True,autoincrement=True,nullable=False)
    name         = sa.Column(sa.String(128))
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    trash        = sa.Column(sa.Boolean,nullable=False,default=False)


class CmmProductsGridDistribution(db.Model,SerializerMixin):
    id_grid    = sa.Column(sa.Integer,primary_key=True,nullable=False)
    color      = sa.Column(sa.String(10),primary_key=True,nullable=False)
    size       = sa.Column(sa.String(5),primary_key=True,nullable=False)
    value      = sa.Column(sa.Integer,nullable=False)
    is_percent = sa.Column(sa.Boolean,nullable=False,default=False)


class CmmLegalEntities(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = sa.Column(sa.String(255),nullable=False)
    taxvat       = sa.Column(sa.String(30),nullable=False,comment="CPF ou CNPJ no Brasil")
    state_region = sa.Column(sa.CHAR(2),nullable=False)
    city         = sa.Column(sa.String(100),nullable=False)
    postal_code  = sa.Column(sa.String(30),nullable=False)
    neighborhood = sa.Column(sa.String(150),nullable=False)
    phone        = sa.Column(sa.String(30),nullable=False)
    email        = sa.Column(sa.String(150),nullable=False)
    type         = sa.Column(sa.CHAR(1),nullable=False,default='C',comment="C = Customer(Cliente), R = Representative(Representante), S = Supplier(Fornecedor)")
    trash        = sa.Column(sa.Boolean,nullable=False,default=False)
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())


class B2bCustomersGroup(db.Model,SerializerMixin):
    id               = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name             = sa.Column(sa.String(128),nullable=False)
    need_approvement = sa.Column(sa.Boolean,nullable=False,)
    date_created     = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated     = sa.Column(sa.DateTime,onupdate=func.now())
    trash            = sa.Column(sa.Boolean,nullable=False,default=False)


class B2bCustomerGroupCustomer(db.Model,SerializerMixin):
    id_group    = sa.Column(sa.Integer,primary_key=True)
    id_customer = sa.Column(sa.Integer,primary_key=True,comment="Id da tabela CmmLegalEntities quando type=C")


class B2bCustomerGroupRepresentative(db.Model,SerializerMixin):
    id_group          = sa.Column(sa.Integer,primary_key=True)
    id_representative = sa.Column(sa.Integer,primary_key=True,comment="Id da tabela CmmLegalEntities quando type=R")


class B2bOrders(db.Model,SerializerMixin):
    id                   = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    id_customer          = sa.Column(sa.Integer,nullable=False)
    id_payment_condition = sa.Column(sa.Integer,nullable=False)
    make_online          = sa.Column(sa.Boolean,nullable=False,default=True,comment="Os pedidos do sistema podem ser online ou offline")
    date_created         = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated         = sa.Column(sa.DateTime,onupdate=func.now())
    trash                = sa.Column(sa.Boolean,nullable=False,default=False)


class B2bOrdersProducts(db.Model,SerializerMixin):
    id_order   = sa.Column(sa.Integer,nullable=False,primary_key=True)
    id_product = sa.Column(sa.Integer,nullable=False,primary_key=True)
    color      = sa.Column(sa.String(10),primary_key=True,nullable=False)
    size       = sa.Column(sa.String(5),primary_key=True,nullable=False)
    quantity   = sa.Column(sa.Integer,nullable=False)
    price      = sa.Column(sa.Float,nullable=False)
    discount   = sa.Column(sa.Numeric(5,2))
    discount_percentage = sa.Column(sa.Numeric(5,2))


class B2bTablePrice(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,nullable=False,primary_key=True,autoincrement=True)
    name         = sa.Column(sa.String(128),nullable=False)
    start_date   = sa.Column(sa.DateTime)
    end_date     = sa.Column(sa.DateTime)
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    active       = sa.Column(sa.Boolean,nullable=False,default=True)


class B2bTablePriceProduct(db.Model,SerializerMixin):
    id_table_price = sa.Column(sa.Integer,nullable=False,primary_key=True)
    id_product     = sa.Column(sa.Integer,nullable=False,primary_key=True)
    stock_quantity = sa.Column(sa.Integer,nullable=False)
    price          = sa.Column(sa.Numeric(5,2),nullable=False,comment="Valor de Preço do Atacado")
    price_retail   = sa.Column(sa.Numeric(5,2),nullable=False,comment="Valor de Preço do Varejo")


class B2bPaymentConditions(db.Model,SerializerMixin):
    id            = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name          = sa.Column(sa.String(100),nullable=False)
    received_days = sa.Column(sa.SmallInteger,nullable=False,default=1,comment="Dias para receber o valor")
    installments  = sa.Column(sa.SmallInteger,nullable=False,default=1,comment="Número de parcelas")
    date_created  = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated  = sa.Column(sa.DateTime,onupdate=func.now())
    trash         = sa.Column(sa.Boolean,nullable=False,default=False)


class B2bCollection(db.Model,SerializerMixin):
    id            = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name          = sa.Column(sa.String(128),nullable=False)
    date_created  = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated  = sa.Column(sa.DateTime,onupdate=func.now())
    trash         = sa.Column(sa.Boolean,nullable=False,default=False)


class B2bCollectionPrice(db.Model,SerializerMixin):
    id_collection  = sa.Column(sa.Integer,primary_key=True,nullable=False)
    id_table_price = sa.Column(sa.Integer,primary_key=True,nullable=False)


class CrmFunnel(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = sa.Column(sa.String(128),nullable=False)
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    trash        = sa.Column(sa.Boolean,nullable=False,default=False)


class CrmFunnelStage(db.Model,SerializerMixin):
    id           = sa.Column(sa.Integer,primary_key=True,nullable=False,autoincrement=True)
    id_funnel    = sa.Column(sa.Integer,nullable=False)
    name         = sa.Column(sa.String(128),nullable=False)
    order        = sa.Column(sa.CHAR(2),nullable=False,default='CD',comment='CD = ')
    date_created = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated = sa.Column(sa.DateTime,onupdate=func.now())
    trash        = sa.Column(sa.Boolean,nullable=False,default=False)


class CrmFunnelStageCustomer(db.Model,SerializerMixin):
    id_funnel_stage = sa.Column(sa.Integer,primary_key=True,nullable=False)
    id_customer     = sa.Column(sa.Integer,primary_key=True,nullable=False)
    date_created    = sa.Column(sa.DateTime,nullable=False,server_default=func.now())
    date_updated    = sa.Column(sa.DateTime,onupdate=func.now())
