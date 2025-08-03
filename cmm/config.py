import importlib
from os import environ
from flask import request
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields

ns_config = Namespace("config",description="Obtem as configuracoes do sistema")

#API Models
cfg_model = ns_config.model(
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

cfg_cep_model = ns_config.model(
    "Cep",{
        "postal_code": fields.String
    }
)

@ns_config.route("/")
class CategoryList(Resource):
    @ns_config.response(HTTPStatus.OK,"Obtem as informações de CEP")
    @ns_config.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_config.doc(body=cfg_cep_model,description="Dados necessários",name="content")
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