from abc import abstractmethod,ABC
from types import SimpleNamespace
from requests import Response,Session
from dotenv import load_dotenv
from os import environ,path
import json

from sqlalchemy import Select, create_engine, Engine

from models.public import SysCities

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class CEP(ABC):
    dbconn:Engine
    nav: Session

    def __init__(self) -> None:
        self.nav = Session()
        conn = str(environ.get("F2B_DB_LIB"))+"://"
        conn += str(environ.get("F2B_DB_USER"))+":"
        conn += str(environ.get("F2B_DB_PASS"))+"@"
        conn += str(environ.get("F2B_DB_HOST"))+"/"
        conn += str(environ.get("F2B_DB_NAME"))
        self.dbconn = create_engine(conn)
        super().__init__()

    def _as_object(self,req:Response,try_convert:bool = False):
        return json.loads(req.text,object_hook=lambda d: SimpleNamespace(**d))
    
    def _get_env(self,name:str)->str:
        return str(environ.get(name))
    
    def _get_city_id(self,ibge:str)->int:
        id = 0
        with self.dbconn.connect() as con:
            exc = con.execute(Select(SysCities.id).where(SysCities.brazil_ibge_code==ibge)).first()
            if exc is not None:
                id = exc.id
            con.close()
        return id
    
    
    @abstractmethod 
    def _get_header(self): pass

    @abstractmethod
    def get_postal_code(self,postal_code:str): pass