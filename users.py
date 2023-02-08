from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

api = Namespace("users",description="Operações para manipular dados de usuários do sistema")
apis = Namespace("groups",description="Operações para manipular grupos de usuários do sistema")

#API Models
user_model = api.model(
    "Usuario",{
        "id": fields.Integer,
        "username": fields.String,
        "password": fields.String,
        "name": fields.String,
        "type": fields.String
    }
)

group_model = apis.model(
    "Grupo",{
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


class User(TypedDict):
    id:int
    username:str
    password:str
    name:str
    type:str


class Group(TypedDict):
    id:int
    name:str
    rule:str

@api.route("/<int:page>")
@api.param("page","Número da página")
class UsersApi(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de usuários",[user_model])
    def get(self,page:int)-> list[User]:

        return False


@api.route("/<int:id>")
@api.param("id","Id do registro")
class UserApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de usuario",user_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,_id:int)->User:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um usuario")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um usuario")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False


@apis.route("/<int:page>")
@apis.param("page","Número da página de registros")
class UserGroupsApi(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem um registro de usuario",user_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,page:int)->str:

        return None

@apis.route("/<int:id>")
@apis.param("id","Id do registro")
class UserGroupApi(Resource):
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->str:

        return None
    
    @apis.response(HTTPStatus.OK.value,"Salva dados de um grupo")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @apis.response(HTTPStatus.OK.value,"Exclui os dados de um grupo")
    @apis.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False