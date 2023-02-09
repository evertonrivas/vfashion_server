from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

api = Namespace("orders",description="Operações para manipular dados de pedidos")

#API Models
order_model = api.model(
    "Order",{
        "id": fields.Integer,
        "idcliente": fields.String,
        "password": fields.String,
        "name": fields.String,
        "type": fields.String
    }
)


#Request parsers
order_request = api.parser()
order_request.add_argument("id",type=int,location="form")
order_request.add_argument("username",type=str,location="form")
order_request.add_argument("password",type=str,location="form")
order_request.add_argument("name",type=str,location="form")
order_request.add_argument("type",type=str,location="form")

class Order(TypedDict):
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
class OrdersList(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de pedidos",[order_model])
    @api.doc(description="Teste de documentacao")
    def get(self,page:int)-> list[Order]:

        return [{
            "id":1,
            "username": "teste",
            "password": "bolinha",
            "name": "Jose",
            "type": "A"
        }]


@api.route("/<int:id>")
@api.param("id","Id do registro")
class OrderApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de pedido",order_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,_id:int)->Order:
        return None

    @api.response(HTTPStatus.OK.value,"Salva dados de um pedido")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um pedido")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        return False