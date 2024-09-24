from abc import abstractmethod,ABC
from dotenv import load_dotenv
from os import environ,path

from sqlalchemy import create_engine

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class ArtifInteli(ABC):
    dbconn = None
    ai_model = None
    env = environ

    def __init__(self) -> None:
        self.dbconn = create_engine(environ.get("F2B_DB_LIB")+"://"+environ.get("F2B_DB_USER")+":"+environ.get("F2B_DB_PASS")+"@"+environ.get("F2B_DB_HOST")+"/"+environ.get("F2B_DB_NAME"))
        super().__init__()
    
    
    @abstractmethod 
    def suggest_email(self,subject:str): pass