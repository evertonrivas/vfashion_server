from typing import IO
from requests import Response,Session
from abc import abstractmethod,ABC
from types import SimpleNamespace
from f2bconfig import ContentType
from dotenv import load_dotenv
from os import environ,path
import json

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class File(ABC):
    nav = None
    env = environ

    def __init__(self) -> None:
        self.nav = Session()
        super().__init__()

    def _as_object(self,req:Response):
        return json.loads(req.text,object_hook=lambda d: SimpleNamespace(**d))

    @abstractmethod
    def _get_header(self,type:ContentType):pass

    @abstractmethod
    def send(self,fName:str,fFolder:str,fContent:IO[bytes]):pass

    @abstractmethod
    def drop(self):pass
    
    @abstractmethod
    def get(self, id:str):pass