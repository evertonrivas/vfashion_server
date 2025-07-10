from requests import Response,Session
from abc import abstractmethod,ABC
from types import SimpleNamespace
from dotenv import load_dotenv
from os import environ,path
import json

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class Shipping(ABC):
    nav:Session
    env = environ

    def __init__(self) -> None:
        self.nav = Session()
        super().__init__()

    def verify_nav(self,_verify:bool = False) -> None:
        self.nav.verify = _verify

    def _as_object(self,req:Response):
        return json.loads(req.text,object_hook=lambda d: SimpleNamespace(**d))

    @abstractmethod
    def _get_header(self):pass

    @abstractmethod
    def tracking(self,_taxvat:str,_invoice:str,_invoice_serie:str|None = None, _cte:str|None = None, _code:str|None = None):pass