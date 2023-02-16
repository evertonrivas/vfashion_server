from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request
from models import B2bPaymentConditions,db

ns_payment = Namespace("payment-conditions",description="Operações para manipular dados de pedidos de compras (carrinho)")

pag_model = ns_payment.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

payment_model = ns_payment.model(
    "PaymentCondition",{
        "id": fields.Integer,
        "name": fields.String,
        "received_days": fields.Integer,
        "installments": fields.Integer,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

list_pay_model = ns_payment.model(
    "Return",{
        "pagination": fields.Nested(pag_model),
        "data": fields.List(fields.Nested(payment_model))
    }
)

class PaymentCondition(TypedDict):
    id:int
    name:str
    received_days:int
    installments:int

@ns_payment.route("/")
class PaymentConditionsList(Resource):

    @ns_payment.response(HTTPStatus.OK.value,"Obtem a lista de condições de pagamento",list_pay_model)
    @ns_payment.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_payment.param("page","Número da página de registros","query",type=int,required=True)
    def get(self):
        rquery = B2bPaymentConditions.query.paginate(page=int(request.args.get("page")),per_page=25)
        return {
            "pagination":{
                "registers": rquery.total,
                "page": int(request.args.get("page")),
                "per_page": rquery.per_page,
                "pages": rquery.pages,
                "has_next": rquery.has_next
            },
            "data":[{
                "id":m.id,
                "name": m.name,
                "received_days": m.received_days,
                "installments": m.installments,
                "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            } for m in rquery.items]
        }

    @ns_payment.response(HTTPStatus.OK.value,"Cria uma nova condição de pagamento no sistema")
    @ns_payment.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova condicao de pagamento!")
    @ns_payment.param("name","Nome da condição de pagamento","formData",required=True)
    @ns_payment.param("received_days","Dias para recebimento","formData",type=int,required=True)
    @ns_payment.param("installments","Número de parcelas","formData",type=int,required=True)
    def post(self)->int:
        try:
            payCond = B2bPaymentConditions()
            payCond.name = request.form.get("name")
            payCond.received_days = request.form.get("received_days")
            payCond.installments  = request.form.get("installments")
            db.session.add(payCond)
            db.session.commit()
            return payCond.id
        except:
            return 0

@ns_payment.route("/<int:id>")
@ns_payment.param("id","Id do registro")
class PaymentConditionApi(Resource):
    @ns_payment.response(HTTPStatus.OK.value,"Obtem um registro de uma condição de pagamento",payment_model)
    @ns_payment.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def get(self,id:int)->PaymentCondition:
        return B2bPaymentConditions.query.get(id).to_dict()

    @ns_payment.response(HTTPStatus.OK.value,"Salva dados de uma condição de pgamento")
    @ns_payment.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_payment.param("name","Nome da condição de pagamento","formData",required=True)
    @ns_payment.param("received_days","Dias para recebimento","formData",type=int,required=True)
    @ns_payment.param("installments","Número de parcelas","formData",type=int,required=True)
    def post(self,id:int)->bool:
        try:
            payCond = B2bPaymentConditions.query.get(id)
            payCond.name = request.form.get("name")
            payCond.received_days = request.form.get("received_days")
            payCond.installments  = request.form.get("installments")
            db.session.add(payCond)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_payment.response(HTTPStatus.OK.value,"Exclui os dados de uma condição de pagamento")
    @ns_payment.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def delete(self,id:int)->bool:
        try:
            payCond = B2bPaymentConditions.query.get(id)
            payCond.trash = True
            db.session.commit()
            return True
        except:
            return False