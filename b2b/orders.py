from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request
from models import B2bOrders,db

ns_order = Namespace("orders",description="Operações para manipular dados de pedidos")

#API Models
pag_model = ns_order.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

prod_order = ns_order.model(
    "Product",{
        "id_product": fields.Integer,
        "quantity": fields.Integer
    }
)

order_model = ns_order.model(
    "Order",{
        "id": fields.Integer,
        "id_customer": fields.Integer,
        "make_online": fields.Boolean,
        "id_payment_condition": fields.Integer,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime,
        "products": fields.List(fields.Nested(prod_order))
    }
)

list_order_model = ns_order.model(
    "Return",{
        "pagination": fields.Nested(pag_model),
        "data": fields.List(fields.Nested(order_model))
    }
)

class ProdOrder(TypedDict):
    id_product:int
    quantity:float

class Order(TypedDict):
    id:int
    id_customer:int
    make_online:bool
    id_payment_condition:int
    products:list[ProdOrder]


####################################################################################
#                  INICIO DAS CLASSES QUE IRAO TRATAR OS  PEDIDOS.                 #
####################################################################################
@ns_order.route("/")
class OrdersList(Resource):
    @ns_order.response(HTTPStatus.OK.value,"Obtem a listagem de pedidos",list_order_model)
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_order.param("page","Número da página de registros","query",type=int,required=True)
    def get(self):

        rquery = B2bOrders.query.paginate(page=int(request.args.get("page")),per_page=25)
        return {
            "pagination":{
                "registers": rquery.total,
                "page": int(request.args.get("page")),
                "per_page": rquery.per_page,
                "pages": rquery.pages,
                "has_next": rquery.has_next
            },
            "data":[{
                "id": m.id,
                "id_customer": m.id_customer,
                "make_online": m.make_online,
                "id_payment_condition": m.id_payment_condition,
                "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S"),
                "produtcts": []
            } for m in rquery.items]
        }

    @ns_order.response(HTTPStatus.OK.value,"Cria um novo pedido")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar pedido!")
    @ns_order.param("id_customer","Código do Cliente","formData",type=int, required=True)
    @ns_order.param("make_online","Informa se o pedido foi feito online","formData",type=bool,required=True,default=True)
    @ns_order.param("id_payment_condition","Código da condição de pagamento","formData",type=int,required=True)
    def post(self)->int:
        try:
            order = B2bOrders()
            order.id_customer = request.form.get("id_customer")
            order.make_online = request.form.get("make_online")
            order.id_payment_condition = request.form.get("id_payment_condition")
            db.session.add(order)
            db.session.commit()
            return order.id
        except:
            return 0


@ns_order.route("/<int:id>")
@ns_order.param("id","Id do registro")
class OrderApi(Resource):

    @ns_order.response(HTTPStatus.OK.value,"Obtem um registro de pedido",order_model)
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->Order:
        return B2bOrders.query.get(id).to_dict()

    @ns_order.response(HTTPStatus.OK.value,"Salva dados de um pedido")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_order.param("id_customer","Código do Cliente","formData",type=int, required=True)
    @ns_order.param("make_online","Informa se o pedido foi feito online","formData",type=bool,required=True,default=True)
    @ns_order.param("id_payment_condition","Código da condição de pagamento","formData",type=int,required=True)
    def post(self,id:int)->bool:
        try:
            order = B2bOrders.query.get(id)
            order.id_customer = request.form.get("id_customer")
            order.make_online = request.form.get("make_online")
            order.id_payment_condition = request.form.get("id_payment_condition")
            db.session.add(order)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_order.response(HTTPStatus.OK.value,"Exclui os dados de um pedido")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        try:
            order = B2bOrders.query.get(id)
            order.trash = True
            db.session.add(order)
            db.session.commit()
            return True
        except:
            return False