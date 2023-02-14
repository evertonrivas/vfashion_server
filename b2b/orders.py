from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request

api = Namespace("orders",description="Operações para manipular dados de pedidos")

#API Models
prod_order = api.model(
    "Product",{
        "idproduct": fields.Integer,
        "quantity": fields.Integer
    }
)

order_model = api.model(
    "Order",{
        "id": fields.Integer,
        "date_created": fields.Integer,
        "idcustomer": fields.Integer,
        "products": fields.List(fields.Nested(prod_order)),
        "make_online": fields.Boolean,
        "idpayment_condition": fields.Integer
    }
)

class ProdOrder(TypedDict):
    idproduct:int
    quantity:float

class Order(TypedDict):
    id:int
    idcustomer:str
    products:list[ProdOrder]


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
            "id": int(request.args.get("page")),
            "idcustomer": "1",
            "products": [{
                "idproduct": 1,
                "quantity": 10
            }]
        }]

    @api.doc(parser=order_model)
    @api.response(HTTPStatus.OK.value,"Cria um novo pedido")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar pedido!")
    def post(self)->int:
        idcustomer = request.form.get("customer")
        if (type(request.form.get("products")) and len(request.form.get("products")) > 0):
            for product in request.form.get("products"):
                print(product)
        return 0


@api.route("/<int:id>")
@api.param("id","Id do registro")
class OrderApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de pedido",order_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->Order:
        return {
            "id": id,
            "idcustomer": "1",
            "products": [{
                "idproduct": 1,
                "quantity": 10
            }]
        }

    @api.doc(parser=order_model)
    @api.response(HTTPStatus.OK.value,"Salva dados de um pedido")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um pedido")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False