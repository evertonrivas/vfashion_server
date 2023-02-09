from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

api = Namespace("users",description="Operações para manipular dados de usuários do sistema")

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


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE USUARIOS.             #
####################################################################################
@api.route("/<int:page>")
@api.param("page","Número da página")
class UsersApi(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de usuários",[user_model])
    @api.doc(description="Teste de documentacao")
    def get(self,page:int)-> list[User]:

        return [{
            "id":1,
            "username": "teste",
            "password": "bolinha",
            "name": "Jose",
            "type": "A"
        }]


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