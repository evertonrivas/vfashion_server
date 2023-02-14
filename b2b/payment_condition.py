from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace

api = Namespace("payment-conditions",description="Operações para manipular dados de pedidos de compras (carrinho)")

payment_model = api.model(
    "PaymentCondition",{
        "id": fields.Integer,
        "name": fields.String,
        "received_days": fields.Integer,
        "installments": fields.Integer
    }
)

class PaymentCondition(TypedDict):
    id:int
    name:str
    received_days:int
    installments:int


@api.route("/")
class PaymentConditionsList(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem a lista de condições de pagamento",[payment_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @api.param("page","Número da página de registros","query",type=int,required=True)
    def get(self)->list[PaymentCondition]:
        return None

    @api.response(HTTPStatus.OK.value,"Cria uma nova condição de pagamento no sistema")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova condicao de pagamento!")
    @api.doc(parser=payment_model)
    def post(self)->int:

        return 0

@api.route("/<int:id>")
class PaymentConditionApi(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem um registro de uma condição de pagamento",payment_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def get(self,id:int)->PaymentCondition:
        return None

    @api.doc(parser=payment_model)
    @api.response(HTTPStatus.OK.value,"Salva dados de uma condição de pgamento")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de uma condição de pagamento")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def delete(self,id:int)->bool:
        return False