import requests
from os import environ
from flask import request
from sqlalchemy import exc
from http import HTTPStatus
from common import _extract_token
from flask_restx import Resource, Namespace, fields

ns_config = Namespace("config",description="Obtem as configuracoes do sistema")

#API Models
cfg_model = ns_config.model(
    "Config",{
        "ai_model": fields.String,
        "ai_api_key": fields.String,
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

@ns_config.route("/")
class ConfigList(Resource):
    @ns_config.response(HTTPStatus.OK,"Obtem as informações de configuração do tenant")
    @ns_config.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    def get(self):
        try:
            if "Authorization" in request.headers:
                tkn = str(request.headers.get("Authorization")).replace("Bearer ","")
                if tkn is not None:
                    token = _extract_token(tkn)
                    if token is not None:
                        resp = requests.post(str(environ.get("F2B_SMC_URL"))+str(token["profile"]),request.get_json())
                        if resp.status_code == HTTPStatus.OK.value:
                            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_config.response(HTTPStatus.OK,"Obtem as informações de CEP")
    @ns_config.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    def post(self):
        try:
            pass
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
# colocar busca do aws da receita e tambem do brasil_aberto