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

class Order(TypedDict):
    id:int
    username:str
    password:str
    name:str
    type:str


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE USUARIOS.             #
####################################################################################
@api.route("/")
class OrdersList(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem a listagem de pedidos",[order_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @api.param("page","Número da página de registros","query",type=int)
    @api.doc(description="Teste de documentacao")
    def get(self)->list[Order]:

        return [{
            "id":1,
            "username": "teste",
            "password": "bolinha",
            "name": "Jose",
            "type": "A"
        }]

    @api.doc(parser=order_model)
    @api.response(HTTPStatus.OK.value,"Cria um novo pedido")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar pedido!")
    def post(self)->int:
        return 0


@api.route("/<int:id>")
@api.param("id","Id do registro")
class OrderApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de pedido",order_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->Order:
        return None

    @api.doc(parser=order_model)
    @api.response(HTTPStatus.OK.value,"Salva dados de um pedido")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um pedido")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False