import logging
from datetime import datetime
from requests import RequestException
from .shipping import Shipping

class Braspress(Shipping):
    def __init__(self) -> None:
        super().__init__()
        self.nav.verify = False

    def _get_header(self):
        self.nav.headers = {
            # "Authorization": ConfigBraspress.TOKEN_TYPE.value+" "+ConfigBraspress.TOKEN_ACCESS.value
            "Authorization": str(self.env.get("F2B_BRASPRESS_TOKEN_TYPE"))+" "+str(self.env.get("F2B_BRASPRESS_TOKEN_ACCESS"))
        }

    def tracking(self, _taxvat: str, _invoice: str, _invoice_serie: str|None = None, _cte: str|None = None, _code:str|None = None):
        self._get_header()
        try:
            resp = self.nav.get('https://api.braspress.com/v'+str(self.env.get("F2B_BRASPRESS_API_VERSION"))+'/tracking/byNf/'+_taxvat+'/'+_invoice+'/json')
            if resp.status_code==200:
                consulta = resp.json()
                
                return [{
                    "shipping": "BRASPRESS",
                    "forecast": datetime.strptime(con['previsaoEntrega'],"%Y-%m-%d").strftime("%d/%m/%Y"),
                    "timeline":[{
                        "date": datetime.strptime(tml['data'],"%Y-%m-%d").strftime("%d/%m/%Y"),
                        "status": tml["descricao"]
                    }for tml in con["timeLine"]]
                }for con in consulta['conhecimentos']]
            
            return False
        except RequestException as e:
            logging.error(e.strerror)
            return False