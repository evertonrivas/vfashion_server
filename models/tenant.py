import json
from os import path
from dotenv import load_dotenv
from types import SimpleNamespace
from f2bconfig import CustomerAction
from helpers import db
from datetime import datetime
from sqlalchemy import ForeignKey, event, func, Column
from sqlalchemy import String, Integer, CHAR, DateTime, Boolean, Text, DECIMAL, SmallInteger, Date

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))


def _get_params(search:str|None):
    if search is not None:
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
            if len(search) > 0:
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

def _save_log(id:int, act:CustomerAction, p_log_action:str):
    log:CmmLegalEntityHistory = CmmLegalEntityHistory()
    setattr(log,"action",act.value)
    setattr(log,"history",p_log_action)
    setattr(log,"id_legal_entity",id)
    setattr(log,"date_created",datetime.now())
    db.session.add(log)
    db.session.commit()

class CmmUserEntity(db.Model):
    id_user     = Column(Integer,nullable=False,primary_key=True)
    id_entity   = Column(Integer,nullable=False,primary_key=True,default=0,comment="Id da tabela CmmLegalEntities")

class CmmCategories(db.Model):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    origin_id    = Column(Integer,nullable=True,index=True)
    name         = Column(String(128),nullable=False)
    id_parent    = Column(Integer,nullable=True)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)


class CmmProducts(db.Model):
    id              = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_type         = Column(Integer,nullable=False,index=True,comment="Campo Id da tabela CmmProductsTypes")
    id_model        = Column(Integer,nullable=False,index=True,comment="Campo Id da tabela CmmProductsModels")
    id_grid         = Column(Integer,nullable=False,index=True,comment="Campo Id da tabela CmmProductsGrid")
    id_collection   = Column(Integer,nullable=True,comment="Campo Id da tabela B2bCollection")
    prodCode        = Column(String(50),nullable=False)
    barCode         = Column(String(128))
    refCode         = Column(String(50),nullable=False)
    name            = Column(String(255),nullable=False)
    description     = Column(String(255))
    observation     = Column(Text,nullable=True)
    ncm             = Column(String(50),nullable=True)
    price           = Column(DECIMAL(10,2),nullable=False)
    price_pos       = Column(DECIMAL(10,2),nullable=True)
    id_measure_unit = Column(Integer,nullable=True,comment="Id da tabela cmm_measure_unit (opcional desde 18/09/2024)")
    structure       = Column(CHAR(1),nullable=False,default='S',comment="S = Simples, C = Composto")
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())
    trash           = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsImport(db.Model):
    id              = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    refCode         = Column(String(50),nullable=False)
    barCode         = Column(String(128))
    type            = Column(String(255),nullable=False)
    model           = Column(String(255),nullable=False)
    brand           = Column(String(255),nullable=False)
    name            = Column(String(255),nullable=False)
    description     = Column(String(255),nullable=True)
    observation     = Column(Text,nullable=True)
    price           = Column(DECIMAL(10,2),nullable=False)
    measure_unit    = Column(String(50),nullable=False)
    color           = Column(String(255),nullable=False)
    size            = Column(String(255),nullable=False)
    quantity        = Column(Integer,nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())

class CmmProductsImages(db.Model):
    id          = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    id_product  = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmProduct")
    img_url     = Column(String(255),nullable=False)
    img_default = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsTypes(db.Model):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    origin_id    = Column(Integer,nullable=True,comment="Utilizado em caso de importacao")
    name         = Column(String(128),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsModels(db.Model):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    origin_id    = Column(Integer,nullable=True,comment="Utilizado em caso de importacao")
    name         = Column(String(255),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmProductsCategories(db.Model):
    id_category  = Column(Integer,primary_key=True,nullable=False)
    id_product   = Column(Integer,primary_key=True,nullable=False)

class CmmProductsGrid(db.Model):
    id           = Column(Integer,primary_key=True,autoincrement=True,nullable=False)
    name         = Column(String(128))
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

# define quais serao os tamanhos utilizados na grade
# serve para garantir a montagem da grade antes de preencher
class CmmProductsGridSizes(db.Model):
    id_grid = Column(Integer,primary_key=True)
    id_size = Column(Integer,primary_key=True)

class CmmProductsGridDistribution(db.Model):
    id_grid    = Column(Integer,primary_key=True,nullable=False)
    id_size    = Column(Integer,primary_key=True,nullable=False)
    value      = Column(Integer,nullable=False)

class CmmMeasureUnit(db.Model):
    id          = Column(Integer,primary_key=True,autoincrement=True)
    code        = Column(CHAR(4),nullable=False)
    description = Column(String(50),nullable=False)
    trash       = Column(Boolean,nullable=False,server_default='0',default=0)

class CmmCountries(db.Model):
    id   = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name = Column(String(100),nullable=False)

class CmmStateRegions(db.Model):
    id         = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_country = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmCoutries")
    name       = Column(String(100),nullable=False)
    acronym    = Column(String(10),nullable=False)

class CmmCities(db.Model):
    id              = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_state_region = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmStateRegions")
    name            = Column(String(100),nullable=False)
    brazil_ibge_code= Column(String(10),nullable=True)

class CmmLegalEntities(db.Model):
    id                = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    origin_id         = Column(Integer,nullable=True,comment="Utilizado em caso de importacao")
    name              = Column(String(255),nullable=False)
    fantasy_name      = Column(String(255),nullable=False)
    taxvat            = Column(String(30),nullable=True,comment="CPF ou CNPJ no Brasil, pode ser nullo por conta de prospeccao")
    id_city           = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmCities")
    postal_code       = Column(String(30),nullable=False)
    neighborhood      = Column(String(150),nullable=False)
    address           = Column(String(255),nullable=False)
    type              = Column(CHAR(1),nullable=False,default='C',server_default='C',comment="C = Customer(Cliente), R = Representative(Representante), S = Supplier(Fornecedor), P = Persona (Pessoa)")
    trash             = Column(Boolean,nullable=False,server_default='0')
    id_import         = Column(Integer,nullable=True,comment="Id da importação realizada pelo CRM, garante que poderá apagar o registro")
    erp_integrated    = Column(Boolean,nullable=False,server_default='0',default=0,comment="Flag de integração com ERP, isso irá garantir a não exclusão em caso de reversão da importação")
    activation_date   = Column(Date,nullable=False)
    inactivation_date = Column(Date,nullable=True)
    date_created      = Column(DateTime,nullable=False,server_default=func.now())
    date_updated      = Column(DateTime,onupdate=func.now())

class CmmLegalEntityContact(db.Model):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
    name            = Column(String(150),nullable=False)
    contact_type    = Column(CHAR(1),nullable=False,server_default='E',default='E',comment='E = E-mail, P = Phone, L = Linkedin, I = Instagram, W = Website, B = Blog, S = Social Media')
    value           = Column(String(200),nullable=False)
    is_whatsapp     = Column(Boolean,nullable=False,default=False)
    is_default      = Column(Boolean,default=False,nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CmmLegalEntityHistory(db.Model):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
    history         = Column(Text,nullable=False)
    action          = Column(CHAR(2),nullable=False,comment='DR = Data Registered,DU = Data Updated, MC = Move CRM Funil/Stage, CS = Chat Message Sended, CR = Chat Message Received, OC = Order Created, OU = Order Update, OD = Order Canceled, SA = System Access, TC = Task Created, FA = File Attached, FD = File Dettached, ES = E-mail Sended, ER = E-mail Replied, RC = Return Created, RU = Return Updated, FB = Financial Bloqued, FU = Financial Unbloqued')
    date_created    = Column(DateTime,nullable=False,server_default=func.now())

class CmmLegalEntityFile(db.Model):
    id              = Column(Integer,primary_key=True,autoincrement=True)
    id_legal_entity = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
    name            = Column(String(255),nullable=False)
    folder          = Column(String(50),nullable=False)
    content_type    = Column(String(100),nullable=False)
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CmmLegalEntityImport(db.Model):
    id               = Column(Integer,primary_key=True,autoincrement=True)
    id_original      = Column(String(11),nullable=True)
    taxvat           = Column(String(30),nullable=False)
    name             = Column(String(255),nullable=False)
    fantasy_name     = Column(String(255),nullable=False)
    city             = Column(String(100),nullable=False)
    postal_code      = Column(String(10),nullable=False)
    neighborhood     = Column(String(100),nullable=False)
    address          = Column(String(255),nullable=False)
    type             = Column(CHAR(1),nullable=False)
    phone_type       = Column(String(100),nullable=True)
    phone_number     = Column(String(50),nullable=True)
    is_whatsapp      = Column(Boolean,nullable=False,server_default='0',default=False)
    phone_is_default = Column(Boolean,nullable=False,server_default='0',default=False)
    email_type       = Column(String(100),nullable=True)
    email_address    = Column(String(255),nullable=True)
    email_is_default = Column(Boolean,nullable=False,server_default='0',default=False)
    date_created     = Column(DateTime,nullable=False,server_default=func.now())

class CmmTranslateColors(db.Model):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    hexcode      = Column(String(8),nullable=True)
    name         = Column(String(100),nullable=False)
    color        = Column(String(100),nullable=False,comment="Original color name")
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())

class CmmTranslateSizes(db.Model):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    new_size     = Column(String(10),nullable=False)
    name         = Column(String(100),nullable=False)
    old_size     = Column(String(5),nullable=False,comment="Original size name")
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())

class CmmReport(db.Model):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = Column(String(255),nullable=False,comment="Nome que aparece para selecionar o relatorio")
    category     = Column(SmallInteger,nullable=False,comment="1 = Clientes, 2 = Calendario, 3 = CRM, 4 = Devoluções, 5 = Pedidos")
    title        = Column(String(255),nullable=False,comment="Titulo quando o relatorio e aberto")
    file_model   = Column(String(100),nullable=False,comment="Arquivo html para formatacao do relatorio")
    filters      = Column(String(255),nullable=False,comment="Filtros que serão aplicados ao relatório")
    master_query = Column(Text,nullable=False)
    master_fields= Column(String(100),nullable=False,comment="Lista de campos que compoem a query master")
    master_where = Column(String(255),nullable=False,comment="condicoes para filtros")
    child_query  = Column(Text,nullable=True)
    child_fileds = Column(String(100),nullable=True,comment="Lista de campos que compoem a query child")
    child_where  = Column(String(255),nullable=True,comment="condicoes para filtros")
    last_query   = Column(Text,nullable=True)
    last_fileds  = Column(String(100),nullable=True,comment="Lista de campos que compoem a query last")
    last_where   = Column(String(255),nullable=True,comment="condicoes para filtros")
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())

class B2bBrand(db.Model):
    id            = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name          = Column(String(100),nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0',default=0)

class B2bCartShopping(db.Model):
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

class B2bCollection(db.Model):
    id            = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_brand      = Column(Integer,nullable=False)
    name          = Column(String(128),nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0',default=0)

class B2bCustomerGroup(db.Model):
    id                = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name              = Column(String(100),nullable=False)
    id_representative = Column(Integer,nullable=True,comment="Id da tabela CmmLegalEntities quando type=R")
    need_approvement  = Column(Boolean,nullable=False,server_default='0',default=0)
    trash             = Column(Boolean,nullable=False,server_default='0',default=0)
    date_created      = Column(DateTime,nullable=False,server_default=func.now())
    date_updated      = Column(DateTime,onupdate=func.now())

class B2bCustomerGroupCustomers(db.Model):
    id_customer_group = Column(Integer,primary_key=True,comment="Id da tabela B2bCustomerGroup")
    id_customer       = Column(Integer,primary_key=True,comment="Id da tabela CmmLegalEntities quando type=C")

class B2bOrders(db.Model):
    id                   = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_customer          = Column(Integer,nullable=False,index=True,comment="Id da tabela CmmLegalEntities")
    id_payment_condition = Column(Integer,nullable=False,index=True,comment="Id da tabela B2bPaymentConditions")
    total_value          = Column(DECIMAL(10,2),nullable=False)
    total_itens          = Column(Integer,nullable=False)
    installments         = Column(SmallInteger,nullable=False)
    installment_value    = Column(DECIMAL(10,2),nullable=False)
    status               = Column(SmallInteger,nullable=False,comment="0 - Enviado, 1 - Em processamento, 2 - Em transporte, 3 - Finalizado")
    integration_number   = Column(Integer,nullable=True,comment="Número do pedido no sistema de cliente")
    track_code           = Column(String(30),nullable=True,comment="Código de rastreamento (apenas para correios)")
    track_company        = Column(String(30),nullable=True,comment="Nome da empresa de transporte")
    invoice_number       = Column(Integer,nullable=True,comment="Número da nota fiscal")
    invoice_serie        = Column(Integer,nullable=True)
    date                 = Column(Date,nullable=False)
    date_created         = Column(DateTime,nullable=False,server_default=func.now())
    date_updated         = Column(DateTime,onupdate=func.now())
    trash                = Column(Boolean,nullable=False,server_default='0',default=0)

class B2bOrdersProducts(db.Model):
    id_order   = Column(Integer,nullable=False,primary_key=True)
    id_product = Column(Integer,nullable=False,primary_key=True)
    id_color   = Column(Integer,primary_key=True,nullable=False)
    id_size    = Column(Integer,primary_key=True,nullable=False)
    quantity   = Column(Integer,nullable=False)
    price      = Column(DECIMAL(10,2),nullable=False)
    discount   = Column(DECIMAL(10,2))
    discount_percentage = Column(DECIMAL(10,2))

class B2bProductStock(db.Model):
    id_product  = Column(Integer,nullable=False,primary_key=True)
    id_color    = Column(Integer,nullable=False,primary_key=True)
    id_size     = Column(Integer,nullable=False,primary_key=True)
    quantity    = Column(SmallInteger,nullable=True)
    in_order    = Column(SmallInteger,nullable=True)
    ilimited    = Column(Boolean,nullable=False,server_default='0')

class B2bTablePrice(db.Model):
    id           = Column(Integer,nullable=False,primary_key=True,autoincrement=True)
    name         = Column(String(128),nullable=False)
    start_date   = Column(DateTime)
    end_date     = Column(DateTime)
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    active       = Column(Boolean,nullable=False,server_default='0',default=0)

class B2bTablePriceProduct(db.Model):
    id_table_price = Column(Integer,nullable=False,primary_key=True)
    id_product     = Column(Integer,nullable=False,primary_key=True)
    price          = Column(DECIMAL(10,2),nullable=False,comment="Valor de Preço do Atacado")
    price_retail   = Column(DECIMAL(10,2),nullable=False,comment="Valor de Preço do Varejo")

class B2bPaymentConditions(db.Model):
    id            = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name          = Column(String(100),nullable=False)
    received_days = Column(SmallInteger,nullable=False,default=1,comment="Dias para receber o valor")
    installments  = Column(SmallInteger,nullable=False,default=1,comment="Número de parcelas")
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
    trash         = Column(Boolean,nullable=False,server_default='0',default=0)

class B2bComissionRepresentative(db.Model):
    id                = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    id_representative = Column(Integer,nullable=False)
    year              = Column(SmallInteger,nullable=False)
    percent           = Column(SmallInteger,nullable=False)
    value             = Column(DECIMAL(10,2),nullable=True)

class B2bTarget(db.Model):
    id             = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    type           = Column(CHAR(1),nullable=False,comment="Y = Year, Q = Quarter, M = Monthly")
    year           = Column(SmallInteger,nullable=False)
    max_value      = Column(SmallInteger,nullable=False)
    value_year     = Column(DECIMAL(10,2),nullable=False)
    value_quarter1 = Column(DECIMAL(10,2),nullable=False)
    value_quarter2 = Column(DECIMAL(10,2),nullable=False)
    value_quarter3 = Column(DECIMAL(10,2),nullable=False)
    value_quarter4 = Column(DECIMAL(10,2),nullable=False)
    value_jan      = Column(DECIMAL(10,2),nullable=False)
    value_feb      = Column(DECIMAL(10,2),nullable=False)
    value_mar      = Column(DECIMAL(10,2),nullable=False)
    value_apr      = Column(DECIMAL(10,2),nullable=False)
    value_may      = Column(DECIMAL(10,2),nullable=False)
    value_jun      = Column(DECIMAL(10,2),nullable=False)
    value_jul      = Column(DECIMAL(10,2),nullable=False)
    value_aug      = Column(DECIMAL(10,2),nullable=False)
    value_sep      = Column(DECIMAL(10,2),nullable=False)
    value_oct      = Column(DECIMAL(10,2),nullable=False)
    value_nov      = Column(DECIMAL(10,2),nullable=False)
    value_dec      = Column(DECIMAL(10,2),nullable=False)


class CrmFunnel(db.Model):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    name         = Column(String(128),nullable=False)
    is_default   = Column(Boolean,nullable=False,server_default='0')
    type         = Column(CHAR(1),nullable=False,server_default='S',comment='S = Salles, P = Prospection')
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class CrmFunnelStage(db.Model):
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

class CrmFunnelStageCustomer(db.Model):
    id_funnel_stage = Column(Integer,primary_key=True,nullable=False)
    id_customer     = Column(Integer,primary_key=True,nullable=False,comment="Id da tabela CmmLegalEntities")
    date_created    = Column(DateTime,nullable=False,server_default=func.now())
    date_updated    = Column(DateTime,onupdate=func.now())

class CrmConfig(db.Model):
    id        = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    cfg_name  = Column(String(100),nullable=False)
    cfg_value = Column(String(255),nullable=False)

class CrmImportation(db.Model):
    id           = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    file         = Column(String(255),nullable=False)
    date_created = Column(DateTime,nullable=False,server_default=func.now())

class FprReason(db.Model):
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

class FprDevolution(db.Model):
    id           = Column(Integer,primary_key=True,autoincrement=True)
    date         = Column(Date,nullable=False)
    id_order     = Column(Integer,index=True,comment="Id da tabela B2bOrders")
    status       = Column(SmallInteger,nullable=False,server_default='0',comment="0 - Salvo, 1 - Em processamento, 2 - Totalmente aprovado, 3 - Parcialmente aprovado, 4 - Reprovado")
    date_created = Column(DateTime,nullable=False,server_default=func.now())
    date_updated = Column(DateTime,onupdate=func.now())
    trash        = Column(Boolean,nullable=False,server_default='0',default=0)

class FprDevolutionItem(db.Model):
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

class ScmCalendar(db.Model):
    time_id       = Column(Integer,primary_key=True,autoincrement=True)
    calendar_date = Column(Date,nullable=False)
    year          = Column(Integer,nullable=False)
    quarter       = Column(Integer,nullable=False)
    month         = Column(Integer,nullable=False)
    week          = Column(Integer,nullable=False)
    day_of_week   = Column(Integer,nullable=False)

class ScmEventType(db.Model):
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

class ScmEvent(db.Model):
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

class ScmFlimv(db.Model):
    id            = Column(Integer,primary_key=True,autoincrement=True)
    frequency     = Column(SmallInteger,nullable=False)
    liquidity     = Column(SmallInteger,nullable=False)
    injury        = Column(SmallInteger,nullable=False)
    mix           = Column(SmallInteger,nullable=False)
    vol_min       = Column(SmallInteger,nullable=False)
    vol_max       = Column(SmallInteger,nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now(),server_default=func.now())
    log_id        = db.relationship('ScmFlimvAudit', backref="scm_flimv_audit", lazy=True)

# tabela serah usada em caso de reconstrucao
# havendo atualizacao do flimv eh necessario gravar aqui
class ScmFlimvAudit(db.Model):
    __tablename__ = "scm_flimv_audit"
    id            = Column(Integer,primary_key=True,autoincrement=True)
    flimv_id      = Column(Integer, ForeignKey('scm_flimv.id'))
    frequency     = Column(SmallInteger,nullable=False)
    liquidity     = Column(SmallInteger,nullable=False)
    injury        = Column(SmallInteger,nullable=False)
    mix           = Column(SmallInteger,nullable=False)
    vol_min       = Column(SmallInteger,nullable=False)
    vol_max       = Column(SmallInteger,nullable=False)
    date_changed  = Column(Date,nullable=False,onupdate=func.now())
    action        = Column(String(50))

@event.listens_for(ScmFlimv,"after_insert")
def insert_flimv_log(mapper,connection,target):
    # esse insert eh para sistemas zerados
    po = ScmFlimvAudit.__table__ # type: ignore
    connection.execute(po.insert().values(
        flimv_id=target.id,
        frequency=target.frequency,
        liquidity=target.liquidity,
        injury=target.injury,
        mix=target.mix,
        vol_min=target.vol_min,
        vol_max=target.vol_max,
        action='insert'))
    
@event.listens_for(ScmFlimv,"after_update")
def update_flimv_log(mapper,connection,target):
    po = ScmFlimvAudit.__table__ # type: ignore
    connection.execute(po.insert().values(
        flimv_id=target.id,
        frequency=target.frequency,
        liquidity=target.liquidity,
        injury=target.injury,
        mix=target.mix,
        vol_min=target.vol_min,
        vol_max=target.vol_max,
        action='update'))

class ScmFlimvResult(db.Model):
    id            = Column(Integer,primary_key=True,autoincrement=True)
    id_customer   = Column(Integer,nullable=False,comment="Id da tabela CmmLegalEntities")
    id_collection = Column(Integer,nullable=False,comment="Id da tabela B2bCollection")
    frequency     = Column(Boolean,nullable=False)
    liquidity     = Column(SmallInteger,nullable=False)
    injury        = Column(SmallInteger,nullable=False)
    mix           = Column(SmallInteger,nullable=False)
    volume        = Column(SmallInteger,nullable=False)
    date_ref      = Column(Date,nullable=False)
    date_created  = Column(DateTime,nullable=False,server_default=func.now())
    date_updated  = Column(DateTime,onupdate=func.now())
