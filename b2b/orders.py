from http import HTTPStatus
from flask_restx import Resource,Namespace
from flask import request
from models import B2bOrders,B2bOrdersProducts,db
from sqlalchemy import exc
import sqlalchemy as sa

ns_order = Namespace("orders",description="Operações para manipular dados de pedidos")
ns_porder = Namespace("orders-products",description="Operações para manipular dados de produtos de pedidos")


####################################################################################
#                  INICIO DAS CLASSES QUE IRAO TRATAR OS  PEDIDOS.                 #
####################################################################################
@ns_order.route("/")
class OrdersList(Resource):
    @ns_order.response(HTTPStatus.OK.value,"Obtem a listagem de pedidos")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_order.param("page","Número da página de registros","query",type=int,required=True)
    @ns_order.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_order.param("query","Texto para busca","query")
    def get(self):
        pag_num  =  1 if request.args.get("page")!=None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")!=None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")!=None else "{}%".format(request.args.get("query"))

        if request.args.get("query")!=None:
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
            order.id_payment_condition = int(request.form.get("id_payment_condition"))
            db.session.add(order)
            db.session.commit()
            return order.id
        except:
            return 0


@ns_order.route("/<int:id>")
@ns_order.param("id","Id do registro")
class OrderApi(Resource):

    @ns_order.response(HTTPStatus.OK.value,"Obtem um registro de pedido")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int):
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


@ns_porder.route("/")
class ProductsOrderList(Resource):
    @ns_porder.response(HTTPStatus.OK.value,"Obtem a listagem de produtos de pedidos")
    @ns_porder.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_porder.param("id_order","Número do pedido","query",type=int,required=True)
    def get(self):
        try:
            rquery = B2bOrdersProducts.query.filter_by(id_order=int(request.args.get("id_order")))
            return [{
                "id_product": m.id_product,
                "color": m.color,
                "size" : m.size,
                "quantity": m.quantity
            } for m in rquery.items]
            
        except exc.SQLAlchemyError as e:
            raise e

    @ns_porder.response(HTTPStatus.OK.value,"Registra produto em um pedido")
    @ns_porder.response(HTTPStatus.BAD_REQUEST.value,"Falha ao associar produto ao pedido!")
    @ns_porder.param("id_order","Id do pedido","formData",type=int,required=True)
    @ns_porder.param("id_product","Id do Produto","formData",type=int,required=True)
    @ns_porder.param("color","Codigo ou nome da cor (hexa ou ingles)","formData",required=True)
    @ns_porder.param("size","Tamanho do produto","formData",required=True)
    @ns_porder.param("quantity","Quantidade do produto","formData",type=int,required=True)
    def post(self):
        try:
            pOrder = B2bOrdersProducts()
            pOrder.id_order   = int(request.form.get("id_order"))
            pOrder.id_product = int(request.form.get("id_product"))
            pOrder.color = request.form.get("color")
            pOrder.size  = request.form.get("size")
            pOrder.quantity = int(request.form.get("quantity"))
            db.session.add(pOrder)
            db.session.commit()
            return True
        except:
            return False