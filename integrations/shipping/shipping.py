from requests import Response,Session
from abc import abstractmethod,ABC
from types import SimpleNamespace
from dotenv import load_dotenv
from os import environ,path
import json

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class Shipping(ABC):
    nav = None
    env = environ

    def __init__(self) -> None:
        self.nav = Session()
        super().__init__()

    def _as_object(self,req:Response):
        return json.loads(req.text,object_hook=lambda d: SimpleNamespace(**d))

    @abstractmethod
    def _get_header(self):pass

    @abstractmethod
    def tracking(self,_taxvat:str,_invoice:str,_invoice_serie:str = None, _cte:str = None, _code:str = None):pass