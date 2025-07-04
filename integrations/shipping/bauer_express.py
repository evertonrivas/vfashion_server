from datetime import datetime
from integrations.shipping import shipping
from requests import RequestException
import logging

class BauerExpress(shipping.Shipping):
    def __init__(self) -> None:
        super().__init__()

    def tracking(self,_taxvat:str,_invoice:str,_invoice_serie:str|None = None, _cte:str|None = None, _code:str|None = None):pass