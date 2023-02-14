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
    def post(self)->int:
        return 0


@api.route("/<int:id>")
@api.param("id","Id do registro")
class CustomerApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de um consumidor",cons_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->Consumer:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um consumidor")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um consumidor")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CONSUMIDORES          #
####################################################################################
@apis.route("/")
class UserGroupsApi(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem um registro de um grupo de consumidores",[group_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @api.param("page","Número da página de registros","query",type=int,required=True)
    def get(self)->list[ConsumerGroup]:

        return None

    @api.doc(parser=group_model)
    @api.response(HTTPStatus.OK.value,"Cria um novo grupo de consumidores")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar grupo de consumidores!")
    def post(self)->int:

        return 0


@apis.route("/<int:id>")
@apis.param("id","Id do registro")
class UserGroupApi(Resource):
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo de consumidores",group_model)
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->ConsumerGroup:

        return None
    
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo de consumidores")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        return False
    
    @apis.response(HTTPStatus.OK.value,"Exclui os dados de um grupo de consumidores")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False