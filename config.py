from enum import Enum

class Config(Enum):
    PAGINATION_SIZE = 25
    EXPIRE_SESSION  = 3600
    
    DB_LIB           = "mysql+pymysql"
    DB_HOST          = "localhost"
    DB_NAME          = "vfashion"
    DB_USER          = "root"
    DB_PASS          = "romero01"
    COMPANY_TAXVAT   = ''
    TRACK_ORDER      = False #will activate track on order history on b2b/orders.py
    CONNECT_ERP      = True #will integrate orders,invoices, customers, representatives and products on task_manager.py
    ERP_MODULE       = "virtualage" #used on task_manager.py. The value is files on integrations folders (except erp)
    ERP_CLASS        = "VirtualAge" #used on task_manager.py
    LOCALE           = "pt_BR" #nao lembro o motivo do locale no python
    TOKEN_KEY        = "SMART2BEE_" #used on cmm/users.py
    APP_PATH         = "d:/development/fast2bee/backend/" #used on cmm/upload.py
    BREVO_API_KEY    = ""
    EMAIL_SEND_FROM  = "evertonrivas@gmail.com"

class ShippingCompany(Enum):
    BRASPRESS = 1
    JADLOG    = 2
    JAMEF     = 3
    ECT       = 4

class ConfigBraspress(Enum):
    API_VERSION  = 3
    TOKEN_TYPE   = 'Basic'
    TOKEN_ACCESS = 'TEJNSU5EVVNUUklBX1BSRDoyWTg3aEx1SGoxOGVja241'

class ConfigJamef(Enum):
    USERNAME = ''
    PASSWORD = ''

class ConfigJadlog(Enum):
    TOKEN_TYPE   = 'Bearer'
    TOKEN_ACCESS = ''

class ConfigECT(Enum):
    token_access = 'ZXZlcnRvbnJpdmFzOnJvbWVybzAx' #username:senha (base64)
    token_type   = 'Basic'


class ConfigVirtualAge(Enum):
    URL           = 'https://api.labellamafia.com.br:9443'
    grant_type    = 'password'
    client_id     = 'labellamafiaapiv2'
    client_secret = '16061138'
    username      = 'apiv2'
    password      = 'api8107'
    ACTIVE_COMPANIES = [1]
    DEFAULT_COMPANY  = 1
    ACTIVE_REPS      = [75413,16803,82466,79759,80008,81975,81973,71793,14336,91171,20,75717,78318,71668,17,5021,82496,91172]

class MailTemplates(Enum):
    DEFAULT = 'mail_template.html'

class CustomerAction(Enum):
    #SA = System Access, TC = Task Created, FA = File Attached, ES = E-mail Sended, ER = E-mail Replied, RC = Return Created, FB = Financial Bloqued/Unbloqued
    DATA_REGISTERED       = 'DR'
    DATA_UPDATED          = 'DU'
    DATA_DELETED          = 'DD'
    MOVE_CRM_FUNNEL       = 'MC'
    CHAT_MESSAGE_SEND     = 'CS'
    CHAT_MESSAGE_RECEIVED = 'CR'
    ORDER_CREATED         = 'OC'
    ORDER_UPDATED         = 'OU'
    ORDER_DELETED         = 'OD'
    SYSTEM_ACCESS         = 'SA'
    TASK_CREATED          = 'TC'
    FILE_ATTACHED         = 'FA'
    FILE_DETTACHED        = 'FD'
    EMAIL_SENDED          = 'ES'
    EMAIL_REPLIED         = 'ER'
    RETURN_CREATED        = 'RC'
    RETURN_UPDATED        = 'RU'
    FINANCIAL_BLOQUED     = 'FB'
    FINANCIAL_UNBLOQUED   = 'FU'
    
class ContactType(Enum):
    EMAIL = 'E'
    PHONE = 'P'