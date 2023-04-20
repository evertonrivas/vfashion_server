from enum import Enum

class Config(Enum):
    PAGINATION_SIZE = 25
    EXPIRE_SESSION  = 3600
    
    DB_LIB  = "mysql+pymysql"
    DB_TYPE = "MYSQL"
    DB_HOST = "localhost"
    DB_NAME = "venda_fashion"
    DB_USER = "venda_fashion"
    DB_PASS = "vd_fashion"
    COMPANY_TAXVAT = ''
    TRACK_ORDER = False
    CONNECT_ERP = True
    ERP_MODULE  = "integrations.virtualage"
    ERP_CLASS   = "VirtualAge"

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
    URL           = ''
    grant_type    = ''
    client_id     = ''
    client_secret = ''
    username      = ''
    password      = ''
    active_companies = [1]
    default_company  = 1