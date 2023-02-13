from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

api = Namespace("customers",description="Operações para manipular dados de clientes")
apis = Namespace("customer-groups",description="Operações para manipular grupos de clientes")

#API Models
cst_model = api.model(
    "Customer",{
        "name": fields.String,
        "taxvat": fields.String,
        "state_region": fields.String,
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
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CLIENTES.             #
####################################################################################
@api.route("/")
class CustomersList(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem a listagem de clientes",[cst_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @api.param("page","Número da página de registros","query",type=int)
    def get(self)-> list[Customer]:

        return [{
            "id":1,
            "username": "teste",
            "password": "bolinha",
            "name": "Jose",
            "type": "A"
        }]

    @api.doc(parser=cst_model)
    @api.response(HTTPStatus.OK.value,"Cria um novo registro de cliente")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar um novo cliente!")
    def post(self)->int:
        return 0



@api.route("/<int:id>")
@api.param("id","Id do registro")
class CustomerApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de cliente",cst_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->Customer:
        return None

    @api.doc(parser=cst_model)
    @api.response(HTTPStatus.OK.value,"Salva dados de um cliente")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um cliente")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CLIENTES.             #
####################################################################################
@apis.route("/")
class UserGroupsApi(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem um registro de um grupo de usuarios",[group_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @apis.param("page","Número da página de registros","query",type=int)
    def get(self)->list[CustomerGroup]:

        return None


    @api.response(HTTPStatus.OK.value,"Cria um novo grupo de usuários no sistema")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    def post(self)->int:

        return 0


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