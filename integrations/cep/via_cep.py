from requests.exceptions import HTTPError 
import logging
from integrations.cep import cep

class ViaCep(cep.CEP):

    def __init__(self) -> None:
        super().__init__()

    def _get_header(self):
        return super()._get_header()
    
    def get_postal_code(self, postal_code: str):
        try:
            resp = self.nav.get("https://viacep.com.br/ws/"+postal_code+"/json/")
            if resp.status_code==200:
                json_resp = self._as_object(resp)
                return {
                    "address": json_resp.logradouro,
                    "neighborhood": json_resp.bairro,
                    "id_city": self._get_city_id(json_resp.ibge)
                }
            else:
                return False
        except HTTPError as e:
            logging.error(e.errno+" - "+e.response+" - "+e.strerror)
            return False