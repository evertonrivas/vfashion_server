from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

api = Namespace("product",description="Operações para manipular dados de produtos")

#API Models
prod_model = api.model(
    "Product",{
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


class Product(TypedDict):
    id:int
    username:str
    password:str
    name:str
    type:str

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE USUARIOS.             #
####################################################################################
@api.route("/<int:page>")
@api.param("page","Número da página")
class ProductsList(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de produto",[prod_model])
    @api.doc(description="Teste de documentacao")
    def get(self,page:int)-> list[Product]:

        return [{
            "id":1,
            "username": "teste",
            "password": "bolinha",
            "name": "Jose",
            "type": "A"
        }]


@api.route("/<int:id>")
@api.param("id","Id do registro")
class ProductApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de produto",prod_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,_id:int)->Product:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um produto")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um produto")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False