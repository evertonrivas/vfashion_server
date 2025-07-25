from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from datetime import datetime
from models.helpers import _get_params, db
from sqlalchemy import Select, exc, asc, desc, or_
from flask_restx import Resource, Namespace, fields
from models.public import SysPayment, SysPlan, SysCustomer

ns_payment = Namespace("payment", description="Operações para manipular dados de pagamentos")

pay_pag_model = ns_payment.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

cst_model = ns_payment.model(
    "Customer",{
        "id": fields.Integer,
        "name": fields.String,
        "taxvat": fields.String
    })

pln_model = ns_payment.model(
    "Plan",{
        "id": fields.Integer,
        "name": fields.String
    })

pay_model = ns_payment.model(
    "Payment",{
        "customer": fields.Nested(cst_model),
        "plan": fields.Nested(pln_model),
        "year": fields.Integer,
        "month": fields.Integer,
        "value": fields.Float,
        "discount": fields.Float,
        "starter": fields.Float,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

plan_return = ns_payment.model(
    "PaymentReturn",{
        "pagination": fields.Nested(pay_pag_model),
        "data": fields.List(fields.Nested(pay_model))
    }
)

@ns_payment.route("/")
class PaymentList(Resource):
    @ns_payment.response(HTTPStatus.OK,"Obtem um registro de um plano",plan_return)
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @ns_payment.param("page","Número da página de registros","query",type=int,required=True)
    @ns_payment.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_payment.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query    = "" if request.args.get("query") is None else str(request.args.get("query"))

        try:
            params    = _get_params(query)
            if params is not None:
                direction = asc if not hasattr(params,'order') else asc if str(params.order).upper()=='ASC' else desc
                order_by  = 'id' if not hasattr(params,'order_by') else params.order_by
                search    = None if not hasattr(params,"search") else params.search
                list_all  = False if not hasattr(params,'list_all') else True

            rquery = Select(SysCustomer.id.label("customer_id"),
                            SysCustomer.name.label("customer_name"),
                            SysCustomer.taxvat.label("customer_taxvat"),
                            SysPlan.id.label("plan_id"),
                            SysPlan.name.label("plan_name"),
                            SysPayment.year,
                            SysPayment.month,
                            SysPayment.value,
                            SysPayment.discount,
                            SysPayment.starter,
                            SysPayment.date_created,
                            SysPayment.date_updated)\
                            .join(SysPlan,SysPlan.id==SysPayment.id_plan)\
                            .join(SysCustomer,SysCustomer.id==SysPayment.id_customer)\
                            .order_by(direction(getattr(SysPayment,order_by)))
            
            if search is not None:
                rquery = rquery.where(
                    or_(
                        SysPlan.name.like("%{}%".format(search)),
                        SysCustomer.name.like("%{}%".format(search)),
                        SysCustomer.taxvat.like("%{}%".format(search))
                ))

            if not list_all:
                pag = db.paginate(rquery,page=pag_num,per_page=pag_size)
                rquery = rquery.limit(pag_size).offset((pag_num - 1) * pag_size)

                retorno = {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next
                    },
                    "data":[{
                        "customer": {
                            "id": m.customer_id,
                            "name": m.customer_name,
                            "taxvat": m.customer_taxvat,
                        },
                        "plan": {
                            "id": m.plan_id,
                            "name": m.plan_name,
                        },
                        "year": m.year,
                        "month": m.month,
                        "value": float(m.value),
                        "discount": float(m.discount),
                        "starter": float(m.starter),
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                    "customer": {
                        "id": m.customer_id,
                        "name": m.customer_name,
                        "taxvat": m.customer_taxvat,
                    },
                    "plan": {
                        "id": m.plan_id,
                        "name": m.plan_name,
                    },
                    "year": m.year,
                    "month": m.month,
                    "value": float(m.value),
                    "discount": float(m.discount),
                    "starter": float(m.starter),
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                } for m in db.session.execute(rquery)]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_payment.response(HTTPStatus.OK,"Cria uma nova marca")
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Falha ao criar registro!")
    @ns_payment.doc(body=pay_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()

            plan:SysPayment  = SysPayment()
            plan.id_customer = req["id_customer"]
            plan.id_plan     = req["id_plan"]
            plan.month       = req["month"]
            plan.year        = req["year"]
            plan.value       = req["value"]
            plan.discount    = req["discount"]
            plan.starter     = req["start"]
            setattr(plan,"date_created",datetime.now())
            db.session.add(plan)
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
        
    @ns_payment.response(HTTPStatus.OK,"Exclui os dados de uma ou mais marcas")
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Falha ao excluir registro!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                plan:SysPayment = SysPayment.query.get(id) # type: ignore
                setattr(plan,"trash",req["toTrash"])
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_payment.route("/<int:id_customer>/<int:id_plan>/<int:month>/<int:year>")
@ns_payment.param("id_customer","Id do cliente")
@ns_payment.param("id_plan","Id do plano")
@ns_payment.param("month","Mês do pagamento")
@ns_payment.param("year","Ano do pagamento")
class PaymentApi(Resource):
    @ns_payment.response(HTTPStatus.OK,"Retorna os dados dados de um pagamento")
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id_customer:int,id_plan:int,month:int,year:int):
        try:
            pquery = SysPayment.query.get((id_customer,id_plan,month,year))
            cquery = SysCustomer.query.get(id_customer)
            mquery = SysPlan.query.get(id_plan)
            if cquery is None or pquery is None or mquery is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST

            return {
                "customer": {
                    "id": cquery.id,
                    "name": cquery.customer_name,
                    "taxvat": cquery.customer_taxvat,
                },
                "plan": {
                    "id": mquery.id,
                    "name": mquery.name,
                },
                "year": pquery.year,
                "month": pquery.month,
                "value": float(pquery.value),
                "discount": float(pquery.discount),
                "starter": float(pquery.starter),
                "date_created": pquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": pquery.date_updated.strftime("%Y-%m-%d %H:%M:%S") if pquery.date_updated is not None else None
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_payment.response(HTTPStatus.OK,"Atualiza os dados de um pagamento")
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @ns_payment.doc(body=pay_model)
    @auth.login_required
    def post(self,id_customer:int,id_plan:int,year:int,month:int):
        try:
            req = request.get_json()
            plan:SysPayment|None = SysPayment.query.get((id_customer,id_plan,year,month))
            if plan is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST
            
            plan.value    = req["value"]
            plan.discount = req["discount"]
            plan.starter  = req["starter"]
            setattr(plan,"date_updated",datetime.now())
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }