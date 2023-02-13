from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

api = Namespace("users",description="Operações para manipular dados de usuários do sistema")

#API Models
user_model = api.model(
    "User",{
        "id": fields.Integer,
        "username": fields.String,
        "password": fields.String,
        "name": fields.String,
        "type": fields.String
    }
)


#Request parsers
#user_request = api.parser()
#user_request.add_argument("id",type=int,location="form")
#user_request.add_argument("username",type=str,location="form")
#user_request.add_argument("password",type=str,location="form")
#user_request.add_argument("name",type=str,location="form")
#user_request.add_argument("type",type=str,location="form")


class User(TypedDict):
    id:int
    username:str
    password:str
    name:str
    type:str

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE USUARIOS.             #
####################################################################################
@api.route("/")
class UsersList(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de usuários",[user_model])
    @api.doc(description="Teste de documentacao")
    @api.param("page","Número da página de registros","query",type=int)
    def get(self)-> list[User]:

        return [{
            "id":1,
            "username": "teste",
            "password": "bolinha",
            "name": "Jose",
            "type": "A"
        }]

    @api.response(HTTPStatus.OK.value,"Cria um novo usuário no sistema")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo usuário!")
    @api.doc(parser=user_model)
    def post(self)->int:

        return 0


@api.route("/<int:id>")
@api.param("id","Id do registro")
class UserApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de usuario",user_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->User:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um usuario")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um usuario")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False