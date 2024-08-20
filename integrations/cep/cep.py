from abc import abstractmethod,ABC
from types import SimpleNamespace
from requests import Response,Session
from dotenv import load_dotenv
from os import environ,path
import json

from sqlalchemy import Select, create_engine

from models import CmmCities

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class CEP(ABC):
    dbconn = None
    nav = None

    def __init__(self) -> None:
        self.nav = Session()
        self.dbconn = create_engine(environ.get("F2B_DB_LIB")+"://"+environ.get("F2B_DB_USER")+":"+environ.get("F2B_DB_PASS")+"@"+environ.get("F2B_DB_HOST")+"/"+environ.get("F2B_DB_NAME"))
        super().__init__()

    def _as_object(self,req:Response,try_convert:bool = False):
        return json.loads(req.text,object_hook=lambda d: SimpleNamespace(**d))
    
    def _get_env(self,name:str):
        return environ.get(name)
    
    def _get_city_id(self,ibge:str):
        id = 0
        with self.dbconn.connect() as con:
            id = con.execute(Select(CmmCities.id).where(CmmCities.brazil_ibge_code==ibge)).first().id
            con.close()
        return id
    
    
    @abstractmethod 
    def _get_header(self): pass

    @abstractmethod
    def get_postal_code(self,postal_code:str): pass