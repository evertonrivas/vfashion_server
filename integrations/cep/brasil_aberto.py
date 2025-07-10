from requests.exceptions import HTTPError 
from requests import Response
import logging
from cep import CEP

class BrasilAberto(CEP):

    def __init__(self) -> None:
        super().__init__()

    def _get_header(self):
        return {
            "Authorization": "Bearer "+self._get_env("F2B_BRASIL_ABERTO_KEY"),
            "Content-Type": "application/json"
        }
    
    def get_postal_code(self, postal_code: str):
        try:
            resp:Response = self.nav.get("https://api.brasilaberto.com/v1/zipcode/"+postal_code)
            if resp.status_code==200:
                return {
                    "address": None if resp is None else resp.json().result.street,
                    "neighborhood": resp.json().result.district,
                    "id_city": self._get_city_id(resp.json().result.ibgeId)
                }
            else:
                return False
        except HTTPError as e:
            logging.error(str(e.errno) + " - " + str(e.response) + " - " + str(e.strerror))
            return False