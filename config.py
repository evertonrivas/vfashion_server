import enum

class Config(enum.Enum):
    PAGINATION_SIZE = 25
    EXPIRE_SESSION  = 3600
    
    DB_TYPE = "MYSQL"
    DB_HOST = "localhost"
    DB_NAME = "venda_fashion"
    DB_USER = "venda_fashion"
    DB_PASS = "vd_fashion"