import json
from os import environ, path
from dotenv import load_dotenv
from types import SimpleNamespace
from abc import abstractmethod, ABC
from requests import Response, Session
from sqlalchemy import create_engine, Engine

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))


class ERP(ABC):
    nav: Session
    dbconn: Engine

    def __init__(self, schema:str) -> None:
        self.nav = Session()
        conn = str(environ.get("F2B_DB_LIB"))+"://"
        conn += str(environ.get("F2B_DB_USER"))+":"
        conn += str(environ.get("F2B_DB_PASS"))+"@"
        conn += str(environ.get("F2B_DB_HOST"))+"/"
        conn += str(environ.get("F2B_DB_NAME"))
        conn += "?options=-c%20search_path="+schema
        self.dbconn = create_engine(conn)
        super().__init__()

    
    def _as_object(self,req:Response):
        return json.loads(req.text,object_hook=lambda d: SimpleNamespace(**d))

    @abstractmethod 
    def _get_header(self): pass

    @abstractmethod
    def get_representative(self): pass

    @abstractmethod
    def get_customer(self,taxvat:str): pass

    @abstractmethod
    def get_order(self): pass

    @abstractmethod
    def create_order(self): pass

    @abstractmethod
    def get_invoice(self): pass

    @abstractmethod
    def get_measure_unit(self): pass

    @abstractmethod
    def get_bank_slip(self): pass

    @abstractmethod
    def get_products(self): pass

    @abstractmethod
    def get_payment_conditions(self): pass