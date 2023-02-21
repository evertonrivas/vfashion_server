from http import HTTPStatus
from flask import request
from flask_restx import Resource,Namespace

ns_cart = Namespace("cart",description="Operações para manipular dados de pedidos de compras (carrinho)")

@ns_cart.route("/")
class CartList(Resource):
    def get(self):
        pass

    def post(self)->int:
        return 0

@ns_cart.route("/<int:id>")
@ns_cart.param("id","Id do registro")
class CartApi(Resource):
    
    @ns_cart.response(HTTPStatus.OK.value,"Obtem os dados de um carrinho")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def get(self,id:int):
        return None
    
    @ns_cart.response(HTTPStatus.OK.value,"Atualiza os dados de um pedido")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")

    def post(self,id:int)->bool:
        return False

    @ns_cart.response(HTTPStatus.OK.value,"Exclui os dados de um carrinho")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def delete(self,id:int)->bool:

        return False