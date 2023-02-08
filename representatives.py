from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse
from api import api
from api import ns_rep


#API Models
rep_model = api.model(
    "Representante",{
        "id": fields.Integer,
        "name": fields.String,
    }
)


#Request parsers
rep_request = api.parser()
rep_request.add_argument("id",type=int,location="form")
rep_request.add_argument("name",type=str,location="form")


class User(TypedDict):
    id:int
    username:str
    password:str

@ns_rep.route("/")
class UsersApi(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de representantes",[rep_model])
    def get(self)-> list[User]:
        return False

    @api.response(HTTPStatus.OK.value,"Salva os dados de representantes")
    @api.expect(rep_request)
    def post(self,_id:int)->bool:

        return False

@ns_rep.route("/<int:id>")
class UserApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de um representante",rep_model)
    def get(self,_id:int)->User:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um representante")
    def post(self,_id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um representante")
    def delete(self,_id:int)->bool:
        return False