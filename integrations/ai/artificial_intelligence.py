from abc import abstractmethod,ABC
from dotenv import load_dotenv
from os import environ,path

from sqlalchemy import create_engine

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class ArtificialInteligence(ABC):
    dbconn = None
    ai_model = any
    env = environ
    ai_api_key:str = ""

    def __init__(self,api_key:str) -> None:
        conn = str(environ.get("F2B_DB_LIB"))
        conn += "://"+str(environ.get("F2B_DB_USER"))
        conn += ":"+str(environ.get("F2B_DB_PASS"))+"@"
        conn += str(environ.get("F2B_DB_HOST"))+"/"
        conn += str(environ.get("F2B_DB_NAME"))
        self.dbconn = create_engine(conn)
        self.ai_api_key = api_key
        super().__init__()
    
    
    @abstractmethod 
    def suggest_email(self,subject:str,type:str): pass