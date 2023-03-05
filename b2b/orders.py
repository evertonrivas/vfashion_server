from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bOrders,B2bOrdersProducts,db
from sqlalchemy import exc
import sqlalchemy as sa
from auth import auth

ns_order = Namespace("orders",description="Operações para manipular dados de pedidos")
ns_porder = Namespace("orders-products",description="Operações para manipular dados de produtos de pedidos")

prd_pag_model = ns_order.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

prd_ord_model = ns_order.model(
    "ProductsOrder",{
        "id_product": fields.Integer,
        "color": fields.String,
        "size" : fields.String,
        "quantity": fields.Integer
    }
)

ord_model = ns_order.model(
    "Order",{
        "id": fields.String,
        "id_customer": fields.Integer,
        "make_online": fields.Boolean,
        "id_payment_condition": fields.Integer,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime,
        "products": fields.List(fields.Nested(prd_ord_model))
    }
)

ord_return = ns_order.model(
    "OrderReturn",{
        "pagination": fields.Nested(prd_pag_model),
        "data": fields.List(fields.Nested(ord_model))
    }
)


####################################################################################
#                  INICIO DAS CLASSES QUE IRAO TRATAR OS  PEDIDOS.                 #
####################################################################################
@ns_order.route("/")
class OrdersList(Resource):
    @ns_order.response(HTTPStatus.OK.value,"Obtem a listagem de pedidos",ord_return)
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_order.param("page","Número da página de registros","query",type=int,required=True)
    @ns_order.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_order.param("query","Texto para busca","query")
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
            if search!=None:
                #pensar nos filtros para essa listagem
                rquery = B2bOrders.query.paginate(page=pag_num,per_page=pag_size)
            else:
                rquery = B2bOrders.query.filter(B2bOrders.trash==False).paginate(page=pag_num,per_page=pag_size)

            return {
                "pagination":{
                    "registers": rquery.total,
                    "page": pag_num,
                    "per_page": pag_size,
                    "pages": rquery.pages,
                    "has_next": rquery.has_next
                },
                "data":[{
                    "id": m.id,
                    "id_customer": m.id_customer,
                    "make_online": m.make_online,
                    "id_payment_condition": m.id_payment_condition,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
                } for m in rquery.items]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_order.response(HTTPStatus.OK.value,"Cria um novo pedido")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar pedido!")
    @ns_order.doc(body=ord_model)
    def post(self)->int:
        try:
            req = request.get_json()
            order = B2bOrders()
            order.id_customer = req.id_customer
            order.make_online = req.make_online
            order.id_payment_condition = int(req.id_payment_condition)
            db.session.add(order)
            db.session.commit()

            for it in req.products:
                prd = B2bOrdersProducts()
                prd.id_order   = order.id
                prd.id_product = it.id_product
                prd.color      = it.color
                prd.size       = it.size
                prd.quantity   = it.quantity
                db.session.add(prd)
                db.session.commit()

            return order.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


@ns_order.route("/<int:id>")
@ns_order.param("id","Id do registro")
class OrderApi(Resource):

    @ns_order.response(HTTPStatus.OK.value,"Obtem um registro de pedido",ord_model)
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def get(self,id:int):
        try:
            order = B2bOrders.query.get(id)
            squery = B2bOrdersProducts.query.filter_by(id_order=int(request.args.get("id_order"))).all()
            return {
                "id": order.id,
                "id_customer": order.id_customer,
                "make_online": order.make_online,
                "id_payment_condition": order.id_payment_condition,
                "date_created": order.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": order.date_updated.strftime("%Y-%m-%d %H:%M:%S"),
                "products": [{
                    "id_product": m.id_product,
                    "color": m.color,
                    "size" : m.size,
                    "quantity": m.quantity
                }for m in squery]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


    @ns_order.response(HTTPStatus.OK.value,"Atualiza os dados de um pedido")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_order.doc(body=ord_model)
    #@auth.login_required
    def post(self,id:int)->bool:
        try:
            req = request.get_json()
            order = B2bOrders.query.get(id)
            order.id_customer          = order.id_customer if req.id_customer is None else req.id_customer
            order.make_online          = order.make_online if req.make_online is None else req.make_online
            order.id_payment_condition = order.id_payment_condition if req.id_payment_condition is None else req.id_payment_condition
            db.session.commit()

            #apaga e recria os produtos
            db.session.delete(B2bOrdersProducts()).where(B2bOrdersProducts().id_order==id)
            db.session.commit()

            for it in order.products:
                prd = B2bOrdersProducts()
                prd.id_order = id
                prd.id_product = it.id_product
                prd.color = it.color
                prd.size  = it.size
                prd.quantity = it.quantity
                db.session.add(prd)
                db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_order.response(HTTPStatus.OK.value,"Exclui os dados de um pedido")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def delete(self,id:int)->bool:
        try:
            order = B2bOrders.query.get(id)
            order.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


@ns_porder.route("/<int:id>")
@ns_porder.param("id","Id de registro do pedido")
class ProductsOrderList(Resource):
    @ns_porder.response(HTTPStatus.OK.value,"Obtem a listagem de produtos de pedidos",[prd_ord_model])
    @ns_porder.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_porder.param("id_order","Número do pedido","query",type=int,required=True)
    #@auth.login_required
    def get(self,id:int):
        try:
            rquery = B2bOrdersProducts.query.filter_by(id_order=id)
            return [{
                "id_product": m.id_product,
                "color": m.color,
                "size" : m.size,
                "quantity": m.quantity
            } for m in rquery.items]
            
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    
    @ns_porder.response(HTTPStatus.OK.value,"Remove um produto de um pedido")
    @ns_porder.response(HTTPStatus.BAD_REQUEST.value,"Falha ao excluir produto do pedido!")
    @ns_porder.param("id_product","Id do Produto","formData",type=int,required=True)
    @ns_porder.param("color","Codigo ou nome da cor (hexa ou ingles)","formData",required=True)
    @ns_porder.param("size","Tamanho do produto","formData",required=True)
    #@auth.login_required
    def delete(self,id:int):
        try:
            pOrder = B2bOrdersProducts.query.get([
                id,
                int(request.form.get("id_product")),
                request.form.get("color"),
                request.form.get("size")
            ])
            db.session.delete(pOrder)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }