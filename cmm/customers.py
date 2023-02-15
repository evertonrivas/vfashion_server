from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request

api = Namespace("customers",description="Operações para manipular dados de clientes")
apis = Namespace("customer-groups",description="Operações para manipular grupos de clientes")

#API Models
cst_model = api.model(
    "Customer",{
        "id": fields.Integer,
        "name": fields.String,
        "taxvat": fields.String,
        "state_region": fields.String,
        "city": fields.String,
        "postal_code": fields.String,
        "neighborhood": fields.String,
        "phone": fields.String,
        "email": fields.String
    }
)

class Customer(TypedDict):
    id:int
    name:str
    taxvat:str
    state_region:str
    city:str
    postal_code:str
    neighborhood:str
    phone:str
    email:str

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CLIENTES.             #
####################################################################################
@api.route("/")
class CustomersList(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem a listagem de clientes",[cst_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @api.param("page","Número da página de registros","query",type=int,required=True)
    def get(self)-> list[Customer]:

        return [{
            "id":request.args.get("page"),
            "name": "JOSEFINA LTDA",
            "taxvat": "01.111.222/0001-00",
            "state_region": "SC",
            "city": "Florianópolis",
            "postal_code": "88131300",
            "neighborhood": "Centro",
            "phone": "4899999-8888",
            "email": "josefina_ltda@gmail.com"
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

grp_cst_model = apis.model(
    "CustomerGroup",{
        "id":fields.Integer
    }
)

group_model = apis.model(
    "Group",{
        "id": fields.Integer,
        "name": fields.String,
        "need_approval": fields.Boolean,
        "customers": fields.List(fields.Nested(grp_cst_model))
    }
)

class CustomerGroup(TypedDict):
    id:int
    name:str
    need_approval:bool


@apis.route("/")
class UserGroupsApi(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem um registro de um grupo de usuarios",[group_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @api.param("page","Número da página de registros","query",type=int,required=True)
    def get(self)->list[CustomerGroup]:

        return [{
            "id": request.args.get("page"),
            "name": "Grupo com aprovacao",
            "need_approval":True,
            "customers":[{
                "id":0
            }]
        }]


    @api.response(HTTPStatus.OK.value,"Cria um novo grupo de usuários no sistema")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    def post(self)->int:

        return 0


@apis.route("/<int:id>")
@apis.param("id","Id do registro")
class UserGroupApi(Resource):
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->CustomerGroup:

        return {
            "id": id,
            "name": "Grupo com aprovacao",
            "need_approval":True,
            "customers":[{"id":"10"}]
        }
    
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo",group_model)
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @apis.response(HTTPStatus.OK.value,"Exclui os dados de um grupo")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False