from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, Insert, func,String,Integer,CHAR,DateTime,Boolean,Column,Text,DECIMAL,SmallInteger,Date
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime,timedelta
import jwt
import bcrypt
from config import Config,CustomerAction
import json
from types import SimpleNamespace

db = SQLAlchemy()

def _get_params(search:str):
    if search!=None:
        # verifica se existem os pipes de separacao
        if search.find("||")!=-1:
            #ajusta os parametros para nao vacilar com espacos
            search = search.replace(" ||","||").replace("|| ","")
            #inicia criacao do objeto
            p_obj = "{\n"
            #realiza o primeiro split para segmentar parametro + valor
            for param in search.split("||"):
                #segundo split sem looping para montar os parametros no object
                broken = param.split(" ")
                #se o len for 2 soh tem um valor para o parametro
                if len(broken)==2:
                    p_obj += "\""+broken[0].replace("is:","").replace("can:","").replace(" ","").replace("-","_")+"\": \""+broken[1]+"\",\n"
                else:
                #significa que eh uma string separada por espacos, precisa reconcatenar
                    p_obj += "\""+broken[0].replace("is:","").replace("can:","").replace(" ","").replace("-","_")+"\": \""+' '.join(broken[1:len(broken)])+"\",\n"
            p_obj += "}"
            #ajusta o final do objeto
            p_obj = p_obj.replace(",\n}","\n}")

            #retorna um objeto para realizar a busca
            return json.loads(p_obj,object_hook=lambda d: SimpleNamespace(**d))
        else:
            if len(search)>0:
                p_obj = "{\n"
                broken = search.split( )
                if len(broken)==2:
                    p_obj += "\""+broken[0].replace("is:","").replace("can:","").replace(" ","").replace("-","_")+"\": \""+broken[1]+"\",\n"
                else:
                    p_obj += "\""+broken[0].replace("is:","").replace("can:","").replace(" ","").replace("-","_")+"\": \""+' '.join(broken[1:len(broken)])+"\",\n"
                p_obj += "}"
                p_obj = p_obj.replace(",\n}","\n}")
                return json.loads(p_obj,object_hook=lambda d: SimpleNamespace(**d))
    return None

def _show_query(rquery):
    print(rquery.compile(compile_kwargs={"literal_binds": True}))

def _save_log(id:int,act:CustomerAction,p_log_action:str):
    log = CmmLegalEntityHistory()
    log.action          = act.value
    log.history         = p_log_action
    log.id_legal_entity = id
    log.date_created    = datetime.now()
    db.session.add(log)
    db.session.commit()

class CmmUsers(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    username        = Column(String(100), nullable=False,unique=True)
    password        = Column(String(255), nullable=False)
    type            = Column(CHAR(1),nullable=False,default='L',comment='A = Administrador, L = Lojista, R = Representante, V = Vendedor, C = Company User')
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())
    active          = Column(Boolean,nullable=False,server_default='1')
    token           = Column(String(255),index=True,unique=True)
    token_expire    = Column(DateTime)
    is_authenticate = Column(Boolean,nullable=False,default=False)

    def hash_pwd(self,pwd:str):
        self.password = bcrypt.hashpw(pwd.encode(),bcrypt.gensalt()).decode()
        return self.password
    
    def check_pwd(self,pwd:str):
        return bcrypt.checkpw(pwd,self.password.encode())

    def get_token(self,expires_in:int=Config.EXPIRE_SESSION.value):
        now = datetime.now()
        expire_utc = now + timedelta(seconds=expires_in)
        complete_key = now.year + now.month + now.day

        if self.token and self.token_expire > expire_utc:
            return self.token

        #encode e decode por causa da diferenca de versoes do windows que pode retornar byte array ao inves de str
        self.token = jwt.encode({"username":str(self.username) },Config.TOKEN_KEY.value+str(complete_key)).encode().decode()
        self.token_expire = now + timedelta(seconds=expires_in)
        return self.token
    
    def renew_token(self):
        now = datetime.now()
        expire = now + timedelta(seconds=3600)
        return expire

    def revoke_token(self):
        self.token_expire = datetime.now() - timedelta(seconds=1)

    def logout(self):
        self.is_authenticate = False
        self.token = None

    @staticmethod
    def check_token(token):
        user = CmmUsers.query.filter(CmmUsers.token==token).first()
        if user is None or user.token_expire < datetime.now():
            return None
        return user
IDX_USERNAME = Index("IDX_USERNAME",CmmUsers.username,unique=True)

class CmmUserEntity(db.Model,SerializerMixin):
    id_user     = Column(Integer,nullable=False,primary_key=True)
    id_entity   = Column(Integer,nullable=False,primary_key=True,default=0)
    id_consumer = Column(Integer,nullable=False,primary_key=True,default=0)

class CmmProducts(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_category  = Column(Integer,nullable=False)
    id_type      = Column(Integer,nullable=False)
    id_model     = Column(Integer,nullable=False)
    prodCode     = Column(String(50),nullable=False)
    barCode      = Column(String(128))
    refCode      = Column(String(50),nullable=False)
    name         = Column(String(255),nullable=False)
    description  = Column(String(255))
    observation  = Column(Text)
    ncm          = Column(String(50),nullable=True)
    price        = Column(DECIMAL(10,2),nullable=False)
    price_pdv    = Column(DECIMAL(10,2),nullable=True)
    measure_unit = Column(CHAR(2),nullable=False)
    structure    = Column(CHAR(1),nullable=False,default='S',comment="S = Simples, C = Composto")
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0')

class CmmProductsImages(db.Model,SerializerMixin):
    id          = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    id_product  = Column(Integer,nullable=False)
    img_url     = Column(String(255),nullable=False)
    img_default = Column(Boolean,default=False)

class CmmProductsTypes(db.Model,SerializerMixin):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    origin_id    = Column(Integer,nullable=True)
    name         = Column(String(128),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0')

class CmmProductsModels(db.Model,SerializerMixin):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    origin_id    = Column(Integer,nullable=True)
    name         = Column(String(255),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0')

class CmmProductsCategories(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,autoincrement=True,nullable=False)
    origin_id    = Column(Integer,nullable=True)
    name         = Column(String(128),nullable=False)
    id_parent    = Column(Integer,nullable=True)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0')

class CmmProductsGrid(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,autoincrement=True,nullable=False)
    orign_id     = Column(Integer,nullable=True)
    name         = Column(String(128))
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0')

class CmmProductsGridDistribution(db.Model,SerializerMixin):
    id_grid    = Column(Integer,primary_key=True,nullable=False)
    color      = Column(String(10),primary_key=True,nullable=False)
    size       = Column(String(5),primary_key=True,nullable=False)
    value      = Column(Integer,nullable=False)
    is_percent = Column(Boolean,nullable=False,server_default='0')

class CmmMeasureUnit(db.Model,SerializerMixin):
    id          = Column(Integer,primary_key=True,autoincrement=True)
    code        = Column(CHAR(4),nullable=False)
    description = Column(String(50),nullable=False)
    trash       = Column(Boolean,nullable=False,server_default='0')

class CmmCountries(db.Model,SerializerMixin):
    id   = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name = Column(String(100),nullable=False)

class CmmStateRegions(db.Model,SerializerMixin):
    id         = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_country = Column(Integer,nullable=False)
    name       = Column(String(100),nullable=False)
    acronym    = Column(String(10),nullable=False)

class CmmCities(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_state_region = Column(Integer,nullable=False)
    name            = Column(String(100),nullable=False)
    brazil_ibge_code= Column(String(10),nullable=True)

class CmmLegalEntities(db.Model,SerializerMixin):
    id             = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    origin_id      = Column(Integer,nullable=True)
    name           = Column(String(255),nullable=False)
    fantasy_name   = Column(String(255),nullable=False)
    taxvat         = Column(String(30),nullable=False,comment="CPF ou CNPJ no Brasil")
    id_city        = Column(Integer,nullable=False)
    postal_code    = Column(String(30),nullable=False)
    neighborhood   = Column(String(150),nullable=False)
    address        = Column(String(255),nullable=False)
    type           = Column(CHAR(1),nullable=False,default='C',comment="C = Customer(Cliente), R = Representative(Representante), S = Supplier(Fornecedor)")
    trash          = Column(Boolean,nullable=False,server_default='0')
    id_import      = Column(Integer,nullable=True,comment="Id da importação realizada pelo CRM, garante que poderá apagar o registro")
    erp_integrated = Column(Boolean,nullable=False,server_default='0',comment="Flag de integração com ERP, isso irá garantir a não exclusão em caso de reversão da importação")
    date_created   = Column(DateTime,nullable=False,server_default=func.now())
    date_updated   = Column(DateTime,onupdate=func.now())

class CmmLegalEntityContact(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False)
    name            = Column(String(150),nullable=False)
    contact_type    = Column(CHAR(1),nullable=False,default='E',comment='E = E-mail, P = Phone')
    value           = Column(String(200),nullable=False)
    is_whatsapp     = Column(Boolean,nullable=False,default=False)
    is_default      = Column(Boolean,default=False,nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CmmLegalEntityWeb(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False)
    name            = Column(String(150),nullable=False)
    web_type        = Column(CHAR(1),nullable=False,default='E',comment='W = Website, B = Blog, S = Social Media')
    value           = Column(String(255),nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CmmLegalEntityHistory(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False)
    history         = Column(Text,nullable=False)
    action          = Column(CHAR(2),nullable=False,comment='DR = Data Registered,DU = Data Updated, MC = Move CRM Funil/Stage, CS = Chat Message Sended, CR = Chat Message Received, OC = Order Created, OU = Order Update, OD = Order Canceled, SA = System Access, TC = Task Created, FA = File Attached, FD = File Dettached, ES = E-mail Sended, ER = E-mail Replied, RC = Return Created, RU = Return Updated, FB = Financial Bloqued, FU = Financial Unbloqued')
    date_created    = Column(DateTime,nullable=False,server_default=func.now())

class CmmLegalEntityFile(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False)
    name            = Column(String(255),nullable=False)
    folder          = Column(String(50),nullable=False)
    content_type    = Column(String(100),nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CmmTranslateColors(db.Model,SerializerMixin):
    id      = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    hexcode = Column(String(8),nullable=False)
    name    = Column(String(100),nullable=False)
    color   = Column(String(10),nullable=False,comment="Original color name")
    trash        = Column(Boolean,nullable=False,server_default='0')
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())

class CmmTranslateSizes(db.Model,SerializerMixin):
    id        = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    new_size  = Column(String(10),nullable=False)
    size      = Column(String(5),nullable=False,comment="Original size name")
    trash        = Column(Boolean,nullable=False,server_default='0')
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())

class B2bCustomerRepresentative(db.Model,SerializerMixin):
    id_customer       = Column(Integer,primary_key=True,comment="Id da tabela CmmLegalEntities quando type=C")
    id_representative = Column(Integer,primary_key=True,comment="Id da tabela CmmLegalEntities quando type=R")
    need_approvement  = Column(Boolean,nullable=False)
    date_created      = Column(DateTime,nullable=False,server_default=func.now())
    date_updated      = Column(DateTime,onupdate=func.now())

class B2bOrders(db.Model,SerializerMixin):
    id                   = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_customer          = Column(Integer,nullable=False)
    id_payment_condition = Column(Integer,nullable=False)
    total_value          = Column(DECIMAL(10,2),nullable=False)
    total_itens          = Column(Integer,nullable=False)
    installments         = Column(SmallInteger,nullable=False)
    installment_value    = Column(DECIMAL(10,2),nullable=False)
    integrated           = Column(Boolean,nullable=False,default=True,comment="Indica se o pedido foi integrado com o ERP do cliente (se houver necessidade)")
    integration_number   = Column(Integer,nullable=True,comment="Número do pedido no sistema de cliente")
    track_code           = Column(String(30),nullable=True,comment="Código de rastreamento")
    track_company        = Column(String(30),nullable=True,comment="Nome da empresa de transporte")
    invoice_number       = Column(Integer,nullable=True,comment="Número da nota fiscal")
    invoice_serie        = Column(Integer,nullable=True)
    date_created         = Column(DateTime,nullable=False,server_default=func.now())
    date_updated         = Column(DateTime,onupdate=func.now())
    trash                = Column(Boolean,nullable=False,server_default='0')

class B2bOrdersProducts(db.Model,SerializerMixin):
    id_order   = Column(Integer,nullable=False,primary_key=True)
    id_product = Column(Integer,nullable=False,primary_key=True)
    color      = Column(String(10),primary_key=True,nullable=False)
    size       = Column(String(5),primary_key=True,nullable=False)
    quantity   = Column(Integer,nullable=False)
    price      = Column(DECIMAL(10,2),nullable=False)
    discount   = Column(DECIMAL(10,2))
    discount_percentage = Column(DECIMAL(10,2))

class B2bCartShopping(db.Model,SerializerMixin):
    id_customer = Column(Integer,primary_key=True)
    id_product  = Column(Integer,primary_key=True)
    color       = Column(String(10),primary_key=True)
    size        = Column(String(10),primary_key=True)
    quantity   = Column(Integer,nullable=False)
    price      = Column(DECIMAL(10,2),nullable=False)

class B2bProductStock(db.Model,SerializerMixin):
    id_product  = Column(Integer,nullable=False,primary_key=True)
    color       = Column(String(10),nullable=False,primary_key=True)
    size        = Column(String(5),nullable=False,primary_key=True)
    quantity    = Column(SmallInteger,nullable=True)
    in_order    = Column(SmallInteger,nullable=True)
    limited     = Column(Boolean,default=False)

class B2bTablePrice(db.Model,SerializerMixin):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    name         = Column(String(128),nullable=False)
    start_date   = Column(DateTime)
    end_date     = Column(DateTime)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    active       = Column(Boolean,nullable=False,server_default='1')

class B2bTablePriceProduct(db.Model,SerializerMixin):
    id_table_price = Column(Integer,nullable=False,primary_key=True)
    id_product     = Column(Integer,nullable=False,primary_key=True)
    price          = Column(DECIMAL(10,2),nullable=False,comment="Valor de Preço do Atacado")
    price_retail   = Column(DECIMAL(10,2),nullable=False,comment="Valor de Preço do Varejo")

class B2bPaymentConditions(db.Model,SerializerMixin):
    id            = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name          = Column(String(100),nullable=False)
    received_days = Column(SmallInteger,nullable=False,default=1,comment="Dias para receber o valor")
    installments  = Column(SmallInteger,nullable=False,default=1,comment="Número de parcelas")
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0')

class B2bBrand(db.Model,SerializerMixin):
    id = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name = Column(String(100),nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0')

class B2bCollection(db.Model,SerializerMixin):
    id            = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_brand      = Column(Integer,nullable=False)
    name          = Column(String(128),nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0')

class B2bCollectionPrice(db.Model,SerializerMixin):
    id_collection  = Column(Integer,primary_key=True,nullable=False)
    id_table_price = Column(Integer,primary_key=True,nullable=False)



class CrmFunnel(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = Column(String(128),nullable=False)
    is_default   = Column(Boolean,nullable=False,server_default='0')
    type         = Column(CHAR(1),nullable=False,server_default='S',comment='S = Salles, P = Prospection')
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0')

class CrmFunnelStage(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_funnel    = Column(Integer,nullable=False)
    name         = Column(String(128),nullable=False)
    icon         = Column(String(20),nullable=True)
    color        = Column(String(20),nullable=True)
    order        = Column(Integer,nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0')

class CrmFunnelStageCustomer(db.Model,SerializerMixin):
    id_funnel_stage = Column(Integer,primary_key=True,nullable=False)
    id_customer     = Column(Integer,primary_key=True,nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CrmImportation(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    file         = Column(String(255),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())



class ScmCalendar(db.Model,SerializerMixin):
    time_id       = Column(Integer,primary_key=True,autoincrement=True)
    calendar_date = Column(Date,nullable=False)
    year          = Column(Integer,nullable=False)
    quarter       = Column(Integer,nullable=False)
    month         = Column(Integer,nullable=False)
    week          = Column(Integer,nullable=False)
    day_of_week   = Column(Integer,nullable=False)

class ScmEventType(db.Model,SerializerMixin):
    id             = Column(Integer,primary_key=True,autoincrement=True)
    id_parent      = Column(Integer,nullable=True)
    name           = Column(String(100),nullable=False)
    hex_color      = Column(String(7),nullable=False)
    has_budget     = Column(Boolean,nullable=False,default=False)
    use_collection = Column(Boolean,nullable=False,default=False)
    is_milestone   = Column(Boolean,nullable=False,default=False)
    trash          = Column(Boolean,nullable=False,server_default='0')
    date_created   = Column(DateTime,nullable=False,server_default=func.now())
    date_updated   = Column(DateTime,onupdate=func.now())

class ScmEvent(db.Model,SerializerMixin):
    id            = Column(Integer,primary_key=True,autoincrement=True)
    id_parent     = Column(Integer,nullable=True)
    name          = Column(String(100),nullable=False)
    year          = Column(SmallInteger,nullable=False)
    start_date    = Column(Date,nullable=False)
    end_date      = Column(Date,nullable=True)
    id_event_type = Column(Integer,nullable=False)
    id_collection = Column(Integer,nullable=True)
    budget_value  = Column(DECIMAL(10,2),nullable=True)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0')

class ScmFlimv(db.Model,SerializerMixin):
    id            = Column(Integer,primary_key=True,autoincrement=True)
    frequency     = Column(SmallInteger,nullable=False)
    liquidity     = Column(SmallInteger,nullable=False)
    injury        = Column(SmallInteger,nullable=False)
    mix           = Column(SmallInteger,nullable=False)
    vol_min       = Column(SmallInteger,nullable=False)
    vol_max       = Column(SmallInteger,nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())