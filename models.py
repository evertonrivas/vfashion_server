from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, Insert, func,String,Integer,CHAR,DateTime,Boolean,Column,Text,DECIMAL,SmallInteger,Date
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime,timedelta
import jwt
import bcrypt
from config import CustomerAction
import json
from types import SimpleNamespace
from os import environ

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
        return bcrypt.checkpw(pwd,self.password.encode())

    def get_token(self,expires_in:int=int(environ.get("F2B_EXPIRE_SESSION"))):
        now = datetime.now()
        expire_utc = now + timedelta(seconds=expires_in)
        complete_key = now.year + now.month + now.day

        if self.token and self.token_expire > expire_utc:
            return self.token

        #encode e decode por causa da diferenca de versoes do windows que pode retornar byte array ao inves de str
        self.token = jwt.encode({"username":str(self.username) },str(environ.get("F2B_TOKEN_KEY"))+str(complete_key)).encode().decode()
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
    id_entity   = Column(Integer,nullable=False,primary_key=True,default=0,comment="Id da tabela CmmLegalEntities")

class CmmCategories(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    origin_id    = Column(Integer,nullable=True,index=True)
    name         = Column(String(128),nullable=False)
    id_parent    = Column(Integer,nullable=True)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)


class CmmProducts(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_type      = Column(Integer,nullable=False,index=True,comment="Campo Id da tabela CmmProductsTypes")
    id_model     = Column(Integer,nullable=False,index=True,comment="Campo Id da tabela CmmProductsModels")
    id_grid      = Column(Integer,nullable=False,index=True,comment="Campo Id da tabela CmmProductsGrid")
    id_brand     = Column(Integer,nullable=False,index=True,comment="Campo Id da tabela B2bBrand")
    prodCode     = Column(String(50),nullable=False)
    barCode      = Column(String(128))
    refCode      = Column(String(50),nullable=False)
    name         = Column(String(255),nullable=False)
    description  = Column(String(255))
    observation  = Column(Text,nullable=True)
    ncm          = Column(String(50),nullable=True)
    price        = Column(DECIMAL(10,2),nullable=False)
    price_pdv    = Column(DECIMAL(10,2),nullable=True)
    id_measure_unit = Column(Integer,nullable=False,index=True,comment="Id da tabela cmm_measure_unit")
    structure    = Column(CHAR(1),nullable=False,default='S',comment="S = Simples, C = Composto")
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsImages(db.Model,SerializerMixin):
    id          = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    id_product  = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmProduct")
    img_url     = Column(String(255),nullable=False)
    img_default = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsTypes(db.Model,SerializerMixin):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    origin_id    = Column(Integer,nullable=True,comment="Utilizado em caso de importacao")
    name         = Column(String(128),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsModels(db.Model,SerializerMixin):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    origin_id    = Column(Integer,nullable=True,comment="Utilizado em caso de importacao")
    name         = Column(String(255),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsCategories(db.Model,SerializerMixin):
    id_category  = Column(Integer,primary_key=True,nullable=False)
    id_product   = Column(Integer,primary_key=True,nullable=False)

class CmmProductsGrid(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,autoincrement=True,nullable=False)
    origin_id    = Column(Integer,nullable=True,comment="Utilizado em caso de importacao")
    name         = Column(String(128))
    default      = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsGridDistribution(db.Model,SerializerMixin):
    id_grid    = Column(Integer,primary_key=True,nullable=False)
    id_color   = Column(Integer,primary_key=True,nullable=False)
    id_size    = Column(Integer,primary_key=True,nullable=False)
    value      = Column(Integer,nullable=False)

class CmmMeasureUnit(db.Model,SerializerMixin):
    id          = Column(Integer,primary_key=True,autoincrement=True)
    code        = Column(CHAR(4),nullable=False)
    description = Column(String(50),nullable=False)
    trash       = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmCountries(db.Model,SerializerMixin):
    id   = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name = Column(String(100),nullable=False)

class CmmStateRegions(db.Model,SerializerMixin):
    id         = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_country = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmCoutries")
    name       = Column(String(100),nullable=False)
    acronym    = Column(String(10),nullable=False)

class CmmCities(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_state_region = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmStateRegions")
    name            = Column(String(100),nullable=False)
    brazil_ibge_code= Column(String(10),nullable=True)

class CmmLegalEntities(db.Model,SerializerMixin):
    id             = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    origin_id      = Column(Integer,nullable=True,comment="Utilizado em caso de importacao")
    name           = Column(String(255),nullable=False)
    fantasy_name   = Column(String(255),nullable=False)
    taxvat         = Column(String(30),nullable=False,comment="CPF ou CNPJ no Brasil")
    id_city        = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmCities")
    postal_code    = Column(String(30),nullable=False)
    neighborhood   = Column(String(150),nullable=False)
    address        = Column(String(255),nullable=False)
    type           = Column(CHAR(1),nullable=False,default='C',server_default='C',comment="C = Customer(Cliente), R = Representative(Representante), S = Supplier(Fornecedor), U = System User")
    trash          = Column(Boolean,nullable=False,server_default='0')
    id_import      = Column(Integer,nullable=True,comment="Id da importação realizada pelo CRM, garante que poderá apagar o registro")
    erp_integrated = Column(Boolean,nullable=False,server_default='0',default=0,comment="Flag de integração com ERP, isso irá garantir a não exclusão em caso de reversão da importação")
    date_created   = Column(DateTime,nullable=False,server_default=func.now())
    date_updated   = Column(DateTime,onupdate=func.now())

class CmmLegalEntityContact(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
    name            = Column(String(150),nullable=False)
    contact_type    = Column(CHAR(1),nullable=False,server_default='E',default='E',comment='E = E-mail, P = Phone')
    value           = Column(String(200),nullable=False)
    is_whatsapp     = Column(Boolean,nullable=False,default=False)
    is_default      = Column(Boolean,default=False,nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CmmLegalEntityWeb(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
    name            = Column(String(150),nullable=False)
    web_type        = Column(CHAR(1),nullable=False,server_default='E',default='E',comment='W = Website, B = Blog, S = Social Media')
    value           = Column(String(255),nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CmmLegalEntityHistory(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
    history         = Column(Text,nullable=False)
    action          = Column(CHAR(2),nullable=False,comment='DR = Data Registered,DU = Data Updated, MC = Move CRM Funil/Stage, CS = Chat Message Sended, CR = Chat Message Received, OC = Order Created, OU = Order Update, OD = Order Canceled, SA = System Access, TC = Task Created, FA = File Attached, FD = File Dettached, ES = E-mail Sended, ER = E-mail Replied, RC = Return Created, RU = Return Updated, FB = Financial Bloqued, FU = Financial Unbloqued')
    date_created    = Column(DateTime,nullable=False,server_default=func.now())

class CmmLegalEntityFile(db.Model,SerializerMixin):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
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
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())

class CmmTranslateSizes(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    new_size     = Column(String(10),nullable=False)
    name         = Column(String(100),nullable=False)
    old_size     = Column(String(5),nullable=False,comment="Original size name")
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())

class B2bBrand(db.Model,SerializerMixin):
    id            = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name          = Column(String(100),nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0',default=0)

class B2bCartShopping(db.Model,SerializerMixin):
    id_customer = Column(Integer,primary_key=True)
    id_product  = Column(Integer,primary_key=True)
    id_color    = Column(Integer,primary_key=True)
    id_size     = Column(Integer,primary_key=True)
    quantity    = Column(Integer,nullable=False)
    price       = Column(DECIMAL(10,2),nullable=False)
    user_create = Column(Integer,nullable=False)
    date_create = Column(DateTime,server_default=func.now())
    user_update = Column(Integer,nullable=True)
    date_update = Column(DateTime,onupdate=func.now())

class B2bCollection(db.Model,SerializerMixin):
    id            = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_brand      = Column(Integer,nullable=False)
    name          = Column(String(128),nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0',default=0)

class B2bCustomerGroup(db.Model,SerializerMixin):
    id                = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name              = Column(String(100),nullable=False)
    id_representative = Column(Integer,nullable=True,comment="Id da tabela CmmLegalEntities quando type=R")
    need_approvement  = Column(Boolean,nullable=False,server_default='0',default=0)
    trash             = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created      = Column(DateTime,nullable=False,server_default=func.now())
    date_updated      = Column(DateTime,onupdate=func.now())

class B2bCustomerGroupCustomers(db.Model,SerializerMixin):
    id_customer_group = Column(Integer,primary_key=True,comment="Id da tabela B2bCustomerGroup")
    id_customer       = Column(Integer,primary_key=True,comment="Id da tabela CmmLegalEntities quando type=C")

class B2bOrders(db.Model,SerializerMixin):
    id                   = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_customer          = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
    id_payment_condition = Column(Integer,nullable=False,index=True,comment="Id da tabela B2bPaymentConditions")
    total_value          = Column(DECIMAL(10,2),nullable=False)
    total_itens          = Column(Integer,nullable=False)
    installments         = Column(SmallInteger,nullable=False)
    installment_value    = Column(DECIMAL(10,2),nullable=False)
    status               = Column(SmallInteger,nullable=False,comment="0 - Enviado, 1 - Em processamento, 2 - Em transporte, 3 - Finalizado")
    integration_number   = Column(Integer,nullable=True,comment="Número do pedido no sistema de cliente")
    track_code           = Column(String(30),nullable=True,comment="Código de rastreamento")
    track_company        = Column(String(30),nullable=True,comment="Nome da empresa de transporte")
    invoice_number       = Column(Integer,nullable=True,comment="Número da nota fiscal")
    invoice_serie        = Column(Integer,nullable=True)
    date                 = Column(Date,nullable=False,server_default=func.now())
    date_created         = Column(DateTime,nullable=False,server_default=func.now())
    date_updated         = Column(DateTime,onupdate=func.now())
    trash                = Column(Boolean,nullable=False,server_default='0',default=0)

class B2bOrdersProducts(db.Model,SerializerMixin):
    id_order   = Column(Integer,nullable=False,primary_key=True)
    id_product = Column(Integer,nullable=False,primary_key=True)
    id_color   = Column(Integer,primary_key=True,nullable=False)
    id_size    = Column(Integer,primary_key=True,nullable=False)
    quantity   = Column(Integer,nullable=False)
    price      = Column(DECIMAL(10,2),nullable=False)
    discount   = Column(DECIMAL(10,2))
    discount_percentage = Column(DECIMAL(10,2))

class B2bProductStock(db.Model,SerializerMixin):
    id_product  = Column(Integer,nullable=False,primary_key=True)
    id_color    = Column(Integer,nullable=False,primary_key=True)
    id_size     = Column(Integer,nullable=False,primary_key=True)
    quantity    = Column(SmallInteger,nullable=True)
    in_order    = Column(SmallInteger,nullable=True)
    ilimited    = Column(Boolean,nullable=False,server_default='0')

class B2bTablePrice(db.Model,SerializerMixin):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    name         = Column(String(128),nullable=False)
    start_date   = Column(DateTime)
    end_date     = Column(DateTime)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    active       = Column(Boolean,nullable=False,server_default='0',default=0)

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
    trash         = Column(Boolean,nullable=False,server_default='0',default=0)



class CrmFunnel(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = Column(String(128),nullable=False)
    is_default   = Column(Boolean,nullable=False,server_default='0')
    type         = Column(CHAR(1),nullable=False,server_default='S',comment='S = Salles, P = Prospection')
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CrmFunnelStage(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_funnel    = Column(Integer,nullable=False)
    name         = Column(String(128),nullable=False)
    icon         = Column(String(20),nullable=True)
    icon_color   = Column(String(20),nullable=True)
    color        = Column(String(20),nullable=True)
    order        = Column(Integer,nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CrmFunnelStageCustomer(db.Model,SerializerMixin):
    id_funnel_stage = Column(Integer,primary_key=True,nullable=False)
    id_customer     = Column(Integer,primary_key=True,nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CrmConfig(db.Model,SerializerMixin):
    id        = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    cfg_name  = Column(String(100),nullable=False)
    cfg_value = Column(String(255),nullable=False)

class CrmImportation(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    file         = Column(String(255),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())

class FprReason(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,autoincrement=True)
    description  = Column(String(255),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

# class FprSteps(db.Model):
#     id           = Column(Integer,primary_key=True,autoincrement=True)
#     name         = Column(String(255),nullable=False)
#     date_created = Column(DateTime,nullable=False,server_default=func.now())
#     date_updated = Column(DateTime,onupdate=func.now())
#     trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class FprDevolution(db.Model,SerializerMixin):
    id           = Column(Integer,primary_key=True,autoincrement=True)
    date         = Column(Date,nullable=False,server_default=func.now())
    id_order     = Column(Integer,index=True,comment="Id da tabela B2bOrders")
    status       = Column(SmallInteger,nullable=False,server_default='0',comment="0 - Salvo, 1 - Em processamento, 2 - Totalmente aprovado, 3 - Parcialmente aprovado, 4 - Reprovado")
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class FprDevolutionItem(db.Model,SerializerMixin):
    id_devolution = Column(Integer,primary_key=True,comment="Id da tabela FprDevolution")
    id_product    = Column(Integer,nullable=False,primary_key=True)
    id_color      = Column(Integer,primary_key=True,nullable=False)
    id_size       = Column(Integer,primary_key=True,nullable=False)
    id_reason     = Column(Integer,primary_key=True,comment="Id da tabela FprReason")
    quantity      = Column(Integer,nullable=False)
    status        = Column(Boolean,nullable=True,comment="Null - Não avaliado, 0 - Rejeitado, 1 - Aceito")
    picture_1     = Column(String(255),nullable=True)
    picture_2     = Column(String(255),nullable=True)
    picture_3     = Column(String(255),nullable=True)
    picture_4     = Column(String(255),nullable=True)

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
    create_funnel  = Column(Boolean,nullable=False,default=False)
    trash          = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created   = Column(DateTime,nullable=False,server_default=func.now())
    date_updated   = Column(DateTime,onupdate=func.now())

class ScmEvent(db.Model,SerializerMixin):
    id            = Column(Integer,primary_key=True,autoincrement=True)
    id_parent     = Column(Integer,nullable=True)
    name          = Column(String(100),nullable=False)
    year          = Column(SmallInteger,nullable=False)
    start_date    = Column(Date,nullable=False)
    end_date      = Column(Date,nullable=True)
    id_event_type = Column(Integer,nullable=False,comment="Id da tabela ScmEventType")
    id_collection = Column(Integer,nullable=True,comment="Id da tabela B2bCollection")
    budget_value  = Column(DECIMAL(10,2),nullable=True)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0',default=0)

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