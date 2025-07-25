import logging
from datetime import datetime
from requests import RequestException
from .shipping import Shipping

class Jadlog(Shipping):
    def __init__(self) -> None:
        super().__init__()
        self.verify_nav(False)

    def _get_header(self):
        self.nav.headers = {
            "Authorization": str(self.env.get("F2B_JADLOG_TOKEN_TYPE"))+" "+str(self.env.get("F2B_JADLOG_TOKEN_ACCESS")),
            "Content-type": "application/json"
        }
    
    def tracking(self, _taxvat: str, _invoice: str, _invoice_serie: str|None = None, _cte: str|None = None, _code:str|None = None):
        self._get_header()
        try:
            resp = self.nav.get("https://jadlog.com.br/api/tracking/consultar",data={
                "consulta":[{
                    "df":{
                        "nf": _invoice,
                        "serie": _invoice_serie,
                        "tpDocumento": 2,
                        "cnpjRemetente": _taxvat
                    }
                }]
            })

            if resp.status_code==200:
                consulta = resp.json()

                return [{
                    "shipping":"JADLOG",
                    "forecast": datetime.strptime(cons['previsaoEntrega'],"%Y-%m-%d").strftime("%d/%m/%Y"),
                    "timeline": [{
                        "date": datetime.strptime(evt['data'],"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M"),
                        "status": evt['status']
                    }for evt in cons['tracking']['eventos']]
                }for cons in consulta['consulta']]
            return False
        except RequestException as e:
            logging.error(e.strerror)
            return False