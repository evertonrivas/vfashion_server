from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request
from auth import auth

api = Namespace("consumer",description="Operações para manipular dados de consumidores")
apis = Namespace("consumer-groups",description="Operações para manipular grupos de consumidores")

#API Models
cons_model = api.model(
    "Consumer",{
        "id": fields.Integer,
        "username": fields.String,
        "password": fields.String,
        "name": fields.String,
        "type": fields.String
    }
)

group_model = apis.model(
    "ConsumerGroup",{
        "id": fields.Integer,
        "name": fields.String,
        "rule": fields.String
    }
)

class Consumer(TypedDict):
    id:int
    username:str
    password:str
    name:str
    type:str

class ConsumerGroup(TypedDict):
    id:int
    name:str
    rule:str


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CONSUMIDORES          #
####################################################################################
@api.route("/")
class ConsumerList(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem a listagem de consumidores",[cons_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"")
    @api.param("page","Número da página de registros","query",type=int,required=True)
    #@auth.login_required
    def get(self)-> list[Consumer]:

        return [{
            "id":1,
            "username": "teste",
            "password": "bolinha",
            "name": "Jose",
            "type": "A"
        }]

    @api.doc(parser=cons_model)
    @api.response(HTTPStatus.OK.value,"Cria um novo consumidor")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar consumidor!")
    #@auth.login_required
    def post(self)->int:
        return 0


@api.route("/<int:id>")
@api.param("id","Id do registro")
class CustomerApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de um consumidor",cons_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def get(self,id:int)->Consumer:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um consumidor")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um consumidor")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def delete(self,id:int)->bool:
        return False