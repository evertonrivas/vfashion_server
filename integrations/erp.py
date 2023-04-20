from abc import abstractmethod,ABC
from types import SimpleNamespace
from requests import Response,Session
import json
from config import Config
from sqlalchemy import create_engine

class ERP(ABC):
    nav = None
    dbconn = None

    def __init__(self) -> None:
        self.nav = Session()
        self.dbconn = create_engine(Config.DB_LIB.value+"://"+Config.DB_USER.value+":"+Config.DB_PASS.value+"@"+Config.DB_HOST.value+"/"+Config.DB_NAME.value)
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