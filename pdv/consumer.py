from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

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


#Request parsers
cons_request = api.parser()
cons_request.add_argument("id",type=int,location="form")
cons_request.add_argument("username",type=str,location="form")
cons_request.add_argument("password",type=str,location="form")
cons_request.add_argument("name",type=str,location="form")
cons_request.add_argument("type",type=str,location="form")


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
@api.route("/<int:page>")
@api.param("page","Número da página")
class ConsumerList(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de consumidores",[cons_model])
    def get(self,page:int)-> list[Consumer]:

        return [{
            "id":1,
            "username": "teste",
            "password": "bolinha",
            "name": "Jose",
            "type": "A"
        }]


@api.route("/<int:id>")
@api.param("id","Id do registro")
class CustomerApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de um consumidor",cons_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,_id:int)->Consumer:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um consumidor")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um consumidor")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CONSUMIDORES          #
####################################################################################
@apis.route("/<int:page>")
@apis.param("page","Número da página de registros")
class UserGroupsApi(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem um registro de um grupo de consumidores",[group_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,page:int)->list[ConsumerGroup]:

        return None


@apis.route("/<int:id>")
@apis.param("id","Id do registro")
class UserGroupApi(Resource):
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo de consumidores",group_model)
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->ConsumerGroup:

        return None
    
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo de consumidores")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @apis.response(HTTPStatus.OK.value,"Exclui os dados de um grupo de consumidores")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False