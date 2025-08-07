import requests
import importlib
from os import environ
from flask import request
# from sqlalchemy import exc
from http import HTTPStatus
# from models.helpers import db
# from sqlalchemy import Select
# from common import _extract_token
# from models.public import SysConfig
from flask_restx import Resource, Namespace, fields

ns_integra = Namespace("integration",description="Conecta algumas integrações ao sistema")

#API Models
cfg_model = ns_integra.model(
    "Config",{
        "use_company_custom":fields.Boolean,
        "company_name":fields.String,
        "company_logo":fields.String,
        "company_instagram":fields.String,
        "company_facebook":fields.String,
        "company_linkedin":fields.String,
        "company_max_up_files":fields.Integer,
        "company_max_up_images":fields.Integer,
        "company_use_url_images":fields.Boolean,
        "system_pagination_size":fields.Integer,
    }
)

cfg_cep_model = ns_integra.model(
    "Cep",{
        "postal_code": fields.String
    }
)

@ns_integra.route("/")
class IntegrationApi(Resource):
    @ns_integra.response(HTTPStatus.OK,"Obtem os dados de um CNPJ")
    @ns_integra.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    def get(self):
        try:
            req = request.get_json()
            resp = requests.get(str(environ.get("F2B_RECEITA_API"))+req["cnpj"])
            if resp.status_code == HTTPStatus.OK.value:
                result = resp.json()
                return {
                    "endereco": result.logradouro+","+result.numero,
                    "complemento": result.complemento,
                    "bairro": result.bairro,
                    "cep": result.cep
                }
        except Exception:
            return False


    
    @ns_integra.response(HTTPStatus.OK,"Obtem as informações de CEP")
    @ns_integra.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_integra.doc(body=cfg_cep_model,description="Dados necessários",name="content")
    def post(self):
        try:
            req = request.get_json()
            module = str(environ.get("F2B_CEP_MODULE"))
            class_name = str(environ.get("F2B_CEP_MODULE")).replace("_"," ").title().replace(" ","")
            CEP_OBJ = getattr(
            importlib.import_module('integrations.cep.'+module),
            class_name
            )
            cep = CEP_OBJ()
            return cep.get_postal_code(req["postal_code"])
        except Exception:
            return False
    
# colocar busca do aws da receita e tambem do brasil_aberto