from .shipping import Shipping

class Ect(Shipping):
    def __init__(self) -> None:
        super().__init__()

    def tracking(self,_taxvat:str,_invoice:str,_invoice_serie:str|None = None, _cte:str|None = None, _code:str|None = None,_tenant:str|None = None):pass