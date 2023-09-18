from enum import Enum

class Config(Enum):
    PAGINATION_SIZE = 25
    EXPIRE_SESSION  = 3600
    
    DB_LIB  = "mysql+pymysql"
    DB_HOST = "localhost"
    DB_NAME = "vfashion"
    DB_USER = "root"
    DB_PASS = "romero01"
    COMPANY_TAXVAT = ''
    TRACK_ORDER = False
    CONNECT_ERP = True
    ERP_MODULE  = "integrations.virtualage"
    ERP_CLASS   = "VirtualAge"
    LOCALE      = "pt_BR"
    TOKEN_KEY   = "SMART2BEE_"
    APP_PATH    = "d:/development/venda_fashion/backend/"

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
    pass

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
    

