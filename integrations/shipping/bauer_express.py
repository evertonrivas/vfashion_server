import logging
from datetime import datetime
from .shipping import Shipping
from requests import RequestException


class BauerExpress(Shipping):
    def __init__(self) -> None:
        super().__init__()

    def tracking(self,_taxvat:str,_invoice:str,_invoice_serie:str|None = None, _cte:str|None = None, _code:str|None = None):pass