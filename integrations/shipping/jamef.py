from datetime import datetime
from integrations.shipping import shipping
from requests import RequestException
import logging

class Jamef(shipping.Shipping):
    def __init__(self) -> None:
        super().__init__()
        self.nav.verify = False
    
    def _get_header(self):
        resp = self.nav.post('https://developers.jamef.com.br/login',data={
            "username": self.env.get("F2B_JAMEF_USERNAME"),
            "password": self.env.get("F2B_JAMEF_PASSWORD")
        })
        if resp.status_code==200:
            self.nav.headers = {
                "Authorization": resp.json().token_type+" "+resp.json().access_token
            }
    
    def tracking(self, _taxvat: str, _invoice: str, _invoice_serie: str = None, _cte: str = None, _code:str = None):
        self._get_header()
        try:
            resp = self.nav.post("https://developers.jamef.com.br/rastreamento/ver",{
                "documentoResponsavelPagamento" : str(self.env.get("F2B_COMPANY_TAXVAT")),
                "documentoDestinatario": _taxvat,
                "numeroNotaFiscal": _invoice,
                "numeroSerieNotaFiscal": _invoice_serie
            })
            if resp.status_code==200:
                consulta = resp.json()
                return [{
                    "shipping": "JAMEF",
                    "forecast": datetime.strptime(cons["dataPrevisaoEntrega"],"%d/%m/%y").strftime("%d/%m/%Y"),
                    "timeline": [{
                        "date": datetime.strptime(evt["dataAtualizacao"],"%d/%m/%y %H:%M").strftime("%d/%m/%Y %H:%M"),
                        "status": evt["statusRastreamento"]
                    }for evt in cons["historico"]]
                }for cons in consulta["conhecimentos"]]
            return False
        except RequestException as e:
            logging.error(e.strerror)
            return False