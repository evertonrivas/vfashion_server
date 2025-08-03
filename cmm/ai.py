import importlib
import requests
from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from flask_restx import Resource, Namespace, fields
from common import _extract_token

ns_ai = Namespace("ai",description="Manipula informacoes com IA")


#API Models
cfg_ai_model = ns_ai.model(
    "AI",{
        "text":fields.String
    }
)

@ns_ai.route("/")
class CategoryList(Resource):   
    @ns_ai.response(HTTPStatus.OK.value,"Executa a inteligencia artificial")
    @ns_ai.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_ai.doc(body=cfg_ai_model,description="Dados necessários",name="content")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            if "Authorization" in request.headers:
                tkn = request.headers["Authorization"].replace("Bearer ","")
                if tkn is not None:
                    token = _extract_token(tkn)
                    if token is not None:
                        # faz a chamada para reduzir acoplamento
                        resp = requests.get(str(environ.get("F2B_SMC_URL"))+"/config/",{
                            "tenant": token["profile"]
                        })
                        if resp.status_code==HTTPStatus.OK.value:
                            cfg = resp.json()

                            class_name = str(cfg.ai_model).replace("_"," ").title().replace(" ","")
                            AI_OBJ = getattr(
                            importlib.import_module('integrations.ai.'+str(cfg.ai_model)),
                            class_name
                            )
                            ai = AI_OBJ(cfg.ai_api_key)
                            return ai.suggest_email(req["text"],req["type"])
                        else:
                            return {
                                "error_code": HTTPStatus.BAD_REQUEST.value,
                                "error_details": "Falha ao buscar configurações do sistema",
                                "error_sql": resp.reason
                            }, HTTPStatus.BAD_REQUEST
        except Exception as e:
            print(e)
            return False