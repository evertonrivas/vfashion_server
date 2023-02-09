from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

api = Namespace("customers",description="Operações para manipular dados de clientes")
apis = Namespace("customer-groups",description="Operações para manipular grupos de clientes")

#API Models
cst_model = api.model(
    "Customer",{
        "id": fields.Integer,
        "username": fields.String,
        "password": fields.String,
        "name": fields.String,
        "type": fields.String
    }
)

group_model = apis.model(
    "CustomerGroup",{
        "id": fields.Integer,
        "name": fields.String,
        "rule": fields.String
    }
)


#Request parsers
user_request = api.parser()
user_request.add_argument("id",type=int,location="form")
user_request.add_argument("username",type=str,location="form")
user_request.add_argument("password",type=str,location="form")
user_request.add_argument("name",type=str,location="form")
user_request.add_argument("type",type=str,location="form")


class Customer(TypedDict):
    id:int
    username:str
    password:str
    name:str
    type:str

class CustomerGroup(TypedDict):
    id:int
    name:str
    rule:str


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE USUARIOS.             #
####################################################################################
@api.route("/<int:page>")
@api.param("page","Número da página")
class CustomersList(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de clientes",[cst_model])
    def get(self,page:int)-> list[Customer]:

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

    @api.response(HTTPStatus.OK.value,"Obtem um registro de cliente",cst_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,_id:int)->Customer:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um cliente")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um cliente")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CLIENTES.             #
####################################################################################
@apis.route("/<int:page>")
@apis.param("page","Número da página de registros")
class UserGroupsApi(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem um registro de usuario",[group_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,page:int)->list[CustomerGroup]:

        return None


@apis.route("/<int:id>")
@apis.param("id","Id do registro")
class UserGroupApi(Resource):
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo",group_model)
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->CustomerGroup:

        return None
    
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @apis.response(HTTPStatus.OK.value,"Exclui os dados de um grupo")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False