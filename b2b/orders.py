from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmProducts, CmmTranslateColors, CmmTranslateSizes, _save_log, db,_get_params,B2bCartShopping, B2bOrders,B2bOrdersProducts, B2bPaymentConditions, CmmLegalEntities,ScmEvent,ScmEventType
from sqlalchemy import exc,Select,Delete,asc,desc,func,between
import simplejson
from auth import auth
from config import Config, CustomerAction
from decimal import Decimal
from integrations.shipping import Shipping,ShippingCompany
from datetime import datetime

ns_order = Namespace("orders",description="Operações para manipular dados de pedidos")

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
        "quantity": fields.Integer,
        "price": fields.Float,
        "discount": fields.Float,
        "discount_percentage": fields.Float
    }
)

ord_model = ns_order.model(
    "Order",{
        "id": fields.String,
        "id_customer": fields.Integer,
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
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query   = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params    = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            trash     = True if hasattr(params,'active')==False else False #foi invertido
            list_all  = False if hasattr(params,'list_all')==False else True


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
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
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
    @auth.login_required
    def post(self)->int:
        try:
            req = request.get_json()

            for customer in req['customers']:
                order = B2bOrders()
                order.id_customer          = customer
                #order.make_online         = req['make_online']
                order.id_payment_condition = int(req['id_payment_condition'])
                order.installment_value    = req['installment_value']
                order.installments         = req['installments']
                order.status               = 0
                order.total_value          = req['total_value']
                order.total_itens          = req['total_itens']
                order.trash                = False
                db.session.add(order)
                db.session.commit()

                stmt = Select(B2bCartShopping).where(B2bCartShopping.id_customer==customer)

                for cart in db.session.execute(stmt).scalars():
                    prod = B2bOrdersProducts()
                    prod.id_order   = order.id
                    prod.id_product = cart.id_product
                    prod.id_color   = cart.id_color
                    prod.id_size    = cart.id_size
                    prod.price      = cart.price
                    prod.quantity   = cart.quantity
                    prod.discount   = 0
                    prod.discount_percentage = 0
                    db.session.add(prod)
                
                db.session.commit()


                #apaga o conteudo do carrinho de compras que nao se faz mais necessario
                stmt = Delete(B2bCartShopping).where(B2bCartShopping.id_customer==customer)
                db.session.execute(stmt)
                db.session.commit()

                _save_log(customer,CustomerAction.ORDER_CREATED,'Novo pedido realizado ('+order.id+') - em '+datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

            return True
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
    @auth.login_required
    def get(self,id:int):
        try:
            order = db.session.execute(Select(B2bOrders.total_value,
                           B2bOrders.total_itens,
                           B2bOrders.installments,
                           B2bOrders.installment_value,
                           B2bOrders.status,
                           B2bOrders.integration_number,
                           B2bOrders.track_code,
                           B2bOrders.track_company,
                           B2bOrders.invoice_number,
                           B2bOrders.invoice_serie,
                           B2bOrders.date_created,
                           B2bOrders.date_updated,
                           CmmLegalEntities.fantasy_name,
                           B2bOrders.id_customer,
                           B2bOrders.id_payment_condition,
                           B2bPaymentConditions.name.label("payment_condition")
                           )\
                        .join(CmmLegalEntities,CmmLegalEntities.id==B2bOrders.id_customer)\
                        .join(B2bPaymentConditions,B2bPaymentConditions.id==B2bOrders.id_payment_condition)\
                        .where(B2bOrders.id==id)).first()
            iquery = Select(B2bOrdersProducts.id_product,
                            CmmProducts.name,
                            B2bOrdersProducts.id_color,
                            CmmTranslateColors.name.label("color"),
                            B2bOrdersProducts.id_size,
                            CmmTranslateSizes.name.label("size"),
                            B2bOrdersProducts.quantity,
                            B2bOrdersProducts.price,
                            B2bOrdersProducts.discount,
                            B2bOrdersProducts.discount_percentage)\
                        .join(CmmProducts,CmmProducts.id==B2bOrdersProducts.id_product)\
                        .join(CmmTranslateColors,CmmTranslateColors.id==B2bOrdersProducts.id_color)\
                        .join(CmmTranslateSizes,CmmTranslateSizes.id==B2bOrdersProducts.id_size)\
                        .where(B2bOrdersProducts.id_order==id)
            return {
                "id": id,
                "customer": {
                    "id": order.id_customer,
                    "name": order.fantasy_name,
                },
                "payment_condition": {
                    "id": order.id_payment_condition,
                    "name": order.payment_condition
                },
                "total_value": str(order.total_value),
                "total_itens": str(order.total_itens),
                "installments": str(order.installments),
                "installment_value": str(order.installment_value),
                "status": order.status,
                "integration_number": str(order.integration_number),
                "track_code": order.track_code,
                "track_company": order.track_company,
                "invoice_number": str(order.invoice_number),
                "invoice_serie": str(order.invoice_serie),
                "date_created": order.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": None if order.date_updated is None else order.date_updated.strftime("%Y-%m-%d %H:%M:%S"),
                "products": [{
                    "id_order_product": str(m.id_product)+'_'+str(m.id_color)+'_'+str(m.id_size),
                    "id_product": m.id_product,
                    "name": m.name,
                    "id_color": m.id_color,
                    "color": m.color,
                    "id_size": m.id_size,
                    "size" : m.size,
                    "quantity": str(m.quantity),
                    "price": str(m.price),
                    "discount": str(m.discount),
                    "discount_percentage": str(m.discount_percentage)
                }for m in db.session.execute(iquery)]
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
    @auth.login_required
    def post(self,id:int)->bool:
        try:
            # req = request.get_json()
            # order = B2bOrders.query.get(id)
            # order.id_customer          = order.id_customer if req.id_customer is None else req.id_customer
            # order.make_online          = order.make_online if req.make_online is None else req.make_online
            # order.id_payment_condition = order.id_payment_condition if req.id_payment_condition is None else req.id_payment_condition
            # db.session.commit()

            # #apaga e recria os produtos
            # db.session.delete(B2bOrdersProducts()).where(B2bOrdersProducts().id_order==id)
            # db.session.commit()

            # for it in order.products:
            #     prd = B2bOrdersProducts()
            #     prd.id_order = id
            #     prd.id_product = it.id_product
            #     prd.color = it.color
            #     prd.size  = it.size
            #     prd.quantity = it.quantity
            #     db.session.add(prd)
            # db.session.commit()

            # _save_log(req['id_customer'],CustomerAction.ORDER_CREATED,'Pedido atualizado ('+id+') - em '+datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_order.response(HTTPStatus.OK.value,"Exclui os dados de um pedido")
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int)->bool:
        try:
            req   = request.get_json()
            order:B2bOrders = B2bOrders.query.get(id)
            order.trash = True
            db.session.commit()
            if (req["id_customer"]!=0):
                _save_log(req['id_customer'],CustomerAction.ORDER_DELETED,'Pedido ('+id+') cancelado pelo cliente em '+datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            else:
                legal = CmmLegalEntities.query.get(req["id_representative"])
                _save_log(order.id_customer,CustomerAction.ORDER_DELETED,'Pedido ('+id+') cancelado pelo representante ('+legal.name+') em '+datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


class HistoryOrderList(Resource):
    @ns_order.response(HTTPStatus.OK.value,"Obtem a listagem de produtos de pedidos",[prd_ord_model])
    @ns_order.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_order.param("page","Número da página de registros","query",type=int,required=True)
    @ns_order.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_order.param("query","Texto para busca","query")
    @auth.login_required
    def get(self,id:int):
        pag_num   = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query     = "" if request.args.get("query") is None else request.args.get("query")
        try:

            params = _get_params(query)
            order_by  = "id" if hasattr(params,"order_by")==False else params.order_by
            direction = asc if hasattr(params,"order_dir")==False else desc if str(params.order_by).upper()=='DESC' else asc
            list_all  = False if hasattr(params,"list_all")==False else True
            status    = None if hasattr(params,"status")==False else params.status

            stmt = Select(
                          B2bOrders.id.label("id_order"),
                          B2bOrders.date_created,
                          B2bOrders.installment_value,
                          B2bOrders.installments,
                          B2bOrders.total_value,
                          B2bOrders.total_itens,
                          B2bOrders.status,
                          B2bOrders.integration_number,
                          B2bOrders.track_code,
                          B2bOrders.track_company,
                          B2bOrders.invoice_number,
                          B2bOrders.invoice_serie,
                          B2bOrders.id_customer,
                          CmmLegalEntities.name.label("customer_name"),
                          CmmLegalEntities.taxvat,
                          B2bOrders.id_payment_condition,
                          B2bPaymentConditions.name.label("payment_name"))\
                .join(B2bPaymentConditions,B2bPaymentConditions.id==B2bOrders.id_payment_condition)\
                .join(CmmLegalEntities,CmmLegalEntities.id==B2bOrders.id_customer)\
                .order_by(direction(getattr(B2bOrders, order_by)))
            
            if id!=0:
                stmt = stmt.where(B2bOrders.id_customer==id)

            if status is not None:
                stmt = stmt.where(B2bOrders.status==status)
            
            if list_all==False:
                pag = db.paginate(stmt,page=pag_num,per_page=pag_size)
                stmt = stmt.limit(pag_size).offset((pag_num - 1) * pag_size)

                return {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next
                    },
                    "data": [{
                        "id_order": '{:010d}'.format(r.id_order),
                        "id_order_number": r.id_order,
                        "id_customer": r.id_customer,
                        "customer_name": r.customer_name,
                        "id_payment_condition": r.id_payment_condition,
                        "payment_name": r.payment_name,
                        "total_value": simplejson.dumps(Decimal(r.total_value)),
                        "total_itens": r.total_itens,
                        "installments": r.installments,
                        "installment_value": simplejson.dumps(Decimal(r.installment_value)),
                        "status": r.status,
                        "integration_number": r.integration_number,
                        "invoice_number": r.invoice_number,
                        "track": (None if Config.TRACK_ORDER.value==False else self.__getTrack(r.taxvat,r.invoice_number,r.invoice_serie,r.track_company,r.track_code) ),
                        "date_created": r.date_created.strftime("%d/%m/%Y %H:%M:%S")
                    }for r in db.session.execute(stmt)]
                }
            else:
                return [{
                        "id_order": '{:010d}'.format(r.id_order),
                        "id_order_number": r.id_order,
                        "id_customer": r.id_customer,
                        "customer_name": r.customer_name,
                        "id_payment_condition": r.id_payment_condition,
                        "payment_name": r.payment_name,
                        "total_value": simplejson.dumps(Decimal(r.total_value)),
                        "total_itens": r.total_itens,
                        "installments": r.installments,
                        "installment_value": simplejson.dumps(Decimal(r.installment_value)),
                        "status": r.status,
                        "integration_number": r.integration_number,
                        "invoice_number": r.invoice_number,
                        "track": (None if Config.TRACK_ORDER.value==False else self.__getTrack(r.taxvat,r.invoice_number,r.invoice_serie,r.track_company,r.track_code) ),
                        "date_created": r.date_created.strftime("%d/%m/%Y %H:%M:%S")
                    }for r in db.session.execute(stmt)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    def __getTrack(self,_cnpj:str,_nf:int,_nf_serie:int,_emp:str,_code:str):
        opts = {
            "taxvat": _cnpj,
            "invoice": _nf,
            "invoice_serie": _nf_serie
        }

        if _emp=="BRASPRESS":
            return Shipping().tracking(ShippingCompany.BRASPRESS,opts)
        if _emp=="JAMEF":
            return Shipping().tracking(ShippingCompany.JAMEF,opts)
        if _emp=="JADLOG":
            return Shipping().tracking(ShippingCompany.JADLOG,opts)

        return _code
        
ns_order.add_resource(HistoryOrderList,'/history/<int:id>')

class HistoryOrderApi(Resource):
    @auth.login_required
    def get(self):
        try:
            # dt_start = datetime.now()
            # rquery = Select(func.count(B2bOrders.id).label('total'))\
            #     .outerjoin(ScmEvent,ScmEvent.id_collection==B2bOrders.id_collection)\
            #     .where(ScmEvent.start_date<=dt_start).order_by(desc(ScmEvent.start_date))
            # total = db.session.execute(rquery).first()
            return 1
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    #@auth.login_required
    def post(self):
        try:
            # dt_start = datetime.now()
            # rquery = Select(func.sum(B2bOrders.total_value).label('total'))\
            #     .outerjoin(ScmEvent,ScmEvent.id_collection==B2bOrders.id_collection)\
            #     .where(ScmEvent.start_date<=dt_start).order_by(desc(ScmEvent.start_date))
            # total = db.session.execute(rquery).first()
            return 0
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
ns_order.add_resource(HistoryOrderApi,'/total')