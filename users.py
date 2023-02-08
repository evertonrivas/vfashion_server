from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse
from api import api
from api import ns_user


#API Models
user_model = api.model(
    "Usuario",{
        "id": fields.Integer,
        "username": fields.String,
        "password": fields.String,
        "name": fields.String
    }
)


#Request parsers
user_request = api.parser()
user_request.add_argument("id",type=int,location="form")
user_request.add_argument("username",type=str,location="form")
user_request.add_argument("password",type=str,location="form")
user_request.add_argument("name",type=str,location="form")


class User(TypedDict):
    id:int
    username:str
    password:str


@ns_user.route("/")
class UsersApi(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de usuários",[user_model])
    def get(self)-> list[User]:
        return False

    @api.response(HTTPStatus.OK.value,"Salva os dados de usuários")
    @api.expect(user_request)
    def post(self,_id:int)->bool:

        return False


@ns_user.route("/<int:id>")
class UserApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de usuario",user_model)
    def get(self,_id:int)->User:
        return None

    @ns_user.doc("Salva informacoes de um usuario. Se não existir, cria!")
    @api.response(HTTPStatus.OK.value,"Salva dados de um usuario")
    def post(self,_id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um usuario")
    def delete(self,_id:int)->bool:
        return False
