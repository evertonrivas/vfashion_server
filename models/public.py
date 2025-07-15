import jwt
import uuid
import bcrypt
from models.helpers import db as dbForModel
from os import path,environ
from dotenv import load_dotenv
from sqlalchemy import ForeignKey, func, Column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime,timedelta, timezone
from sqlalchemy import DECIMAL, Date,Index, Boolean
from sqlalchemy import String, Integer, CHAR, DateTime

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class SysUsers(dbForModel.Model):
    __bind_key__    = "public"
    __table_args__  = {"schema": "public"}
    id              = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name            = Column(String(255),nullable=False,comment="Nome do usuário")
    username        = Column(String(100), nullable=False,unique=True)
    password        = Column(String(255), nullable=False)
    type            = Column(CHAR(1),nullable=False,default='L',server_default='L',comment='A = Administrador, L = Lojista, I = Lojista (IA), R = Representante, V = Vendedor, C = Company User')
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())
    active          = Column(Boolean,nullable=False,server_default='1',default=1)
    token           = Column(String(255),index=True,unique=True,nullable=True)
    token_expire    = Column(DateTime,nullable=True)
    is_authenticate = Column(Boolean,nullable=False,server_default='0',default=0)

    def hash_pwd(self,pwd:str):
        self.password = bcrypt.hashpw(pwd.encode(),bcrypt.gensalt()).decode()
        return self.password
    
    def check_pwd(self,pwd:str):
        return bcrypt.checkpw(pwd.encode(), self.password.encode())

    def get_token(self,expires_in:int=int(str(environ.get("F2B_EXPIRE_SESSION")))):
        now        = datetime.now(tz=timezone.utc)
        expire_utc = now + timedelta(seconds=expires_in)

        #encode e decode por causa da diferenca de versoes do windows que pode retornar byte array ao inves de str
        self.token        = jwt.encode({"username":str(self.username), "iat": now, "exp": expire_utc},str(environ.get("F2B_TOKEN_KEY"))).encode().decode()
        self.token_expire = expire_utc
        return self.token
    
    def renew_token(self):
        now               = datetime.now(tz=timezone.utc) + timedelta(seconds=int(str(environ.get("F2B_EXPIRE_SESSION"))))
        data_token        = jwt.decode(str(self.token),str(environ.get("F2B_TOKEN_KEY")),algorithms=['HS256'])
        data_token["exp"] = now
        self.token        = jwt.encode(data_token,str(environ.get("F2B_TOKEN_KEY")))
        self.token_expire = now
        return now

    def revoke_token(self):
        self.token_expire = datetime.now() - timedelta(seconds=1)

    def logout(self):
        self.is_authenticate = False
        self.token = None

    @staticmethod
    def check_token(token):
        user = SysUsers.query.filter(SysUsers.token==token).first()
        if user is None or user.token_expire < datetime.now():
            return None
        return user
IDX_USERNAME = Index("IDX_USERNAME",SysUsers.username,unique=True)

class SysCustomer(dbForModel.Model):
    __bind_key__      = "public"
    __table_args__    = {"schema": "public"}
    id                = Column(UUID,primary_key=True,default=uuid.uuid4)
    name              = Column(String(255),nullable=False)
    taxvat            = Column(String(30),nullable=False,comment="CNPJ no Brasil")
    postal_code       = Column(String(30),nullable=False)
    churn             = Column(Boolean,nullable=False,server_default='0',default=0,comment="Indica se o cliente cancelou a assinatura") 
    chur_date         = Column(Date,nullable=True,comment="Data do cancelamento da assinatura") 
    churn_reason     = Column(String(255),nullable=True,comment="Motivo do cancelamento da assinatura")
    date_created      = Column(DateTime,nullable=False,server_default=func.now())
    date_updated      = Column(DateTime,onupdate=func.now())

class SysPlan(dbForModel.Model):
    __bind_key__      = "public"
    __table_args__    = {"schema": "public"}
    id                = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name              = Column(String(50),nullable=False)
    plan_value        = Column(DECIMAL(10,2),nullable=False)
    date_created      = Column(DateTime,nullable=False,server_default=func.now())
    date_updated      = Column(DateTime,onupdate=func.now())

class SysCustomerPlan(dbForModel.Model):
    __bind_key__      = "public"
    __table_args__    = {"schema": "public"}
    id_customer       = Column(ForeignKey(SysCustomer.id),primary_key=True,nullable=False)
    id_plan           = Column(ForeignKey(SysPlan.id),primary_key=True,nullable=False)
    activate          = Column(Boolean,nullable=False,server_default='1',default=1,comment="Indica se o plano está ativo")
    activation_date   = Column(Date,nullable=False)
    inactivation_date = Column(Date,nullable=True)
    payment_model     = Column(CHAR(1),nullable=False,default='M',comment='M = Mensal, Y = Anual')
    payment_method    = Column(CHAR(1),nullable=False,default='C',comment='C = Credit Card, P = Pix, B = Boleto')
    date_created      = Column(DateTime,nullable=False,server_default=func.now())
    date_updated      = Column(DateTime,onupdate=func.now())

class SysCustomerUser(dbForModel.Model):
    __bind_key__   = "public"
    __table_args__ = {"schema": "public"}
    id_customer    = Column(ForeignKey(SysCustomer.id),primary_key=True,nullable=False)
    id_user        = Column(ForeignKey(SysUsers.id),primary_key=True,nullable=False)
