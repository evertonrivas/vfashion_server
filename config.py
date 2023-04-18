from enum import Enum

class Config(Enum):
    PAGINATION_SIZE = 25
    EXPIRE_SESSION  = 3600
    
    DB_TYPE = "MYSQL"
    DB_HOST = "localhost"
    DB_NAME = "venda_fashion"
    DB_USER = "venda_fashion"
    DB_PASS = "vd_fashion"
    COMPANY_TAXVAT = ''


class ShippingCompany(Enum):
    BRASPRESS = 1
    JADLOG    = 2
    JAMEF     = 3

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


class ConfigVirtualAge(Enum):
    URL           = 'https://api.labellamafia.com.br:9443/'
    grant_type    = 'password'
    client_id     = 'labellamafiaapiv2'
    client_secret = '16061138'
    username      = 'apiv2'
    password      = 'api8107'
