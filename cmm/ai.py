from http import HTTPStatus
import importlib
from flask_restx import Resource,Namespace,fields
from auth import auth
from flask import request
from os import environ

ns_ai = Namespace("ai",description="Manipula informacoes com IA")


#API Models
cfg_ai_model = ns_ai.model(
    "AI",{
        "text":fields.String
    }
)

@ns_ai.route("/")
class CategoryList(Resource):   
    @ns_ai.response(HTTPStatus.OK.value,"Obtem as informações de CEP")
    @ns_ai.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_ai.doc(body=cfg_ai_model,description="Dados necessários",name="content")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            module = environ.get("F2B_AI_MODEL")
            class_name = environ.get("F2B_AI_MODEL").replace("_"," ").title().replace(" ","")
            AI_OBJ = getattr(
            importlib.import_module('integrations.ai.'+module),
            class_name
            )
            ai = AI_OBJ()
            return ai.suggest_email(req["text"])
        except Exception as e:
            print(e)
            return False