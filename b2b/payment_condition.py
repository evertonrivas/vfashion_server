from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.helpers import _get_params, db
from sqlalchemy import Select, exc, desc, asc
from models.tenant import B2bPaymentConditions
from flask_restx import Resource,Namespace,fields

ns_payment = Namespace("payment-conditions",description="Operações para manipular dados de condições de pagamento")

pay_pag_model = ns_payment.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

pay_model = ns_payment.model(
    "PaymentCondition",{
        "id": fields.Integer,
        "name": fields.String,
        "received_days": fields.Integer,
        "installments": fields.Integer
    }
)

pay_return = ns_payment.model(
    "PaymentConditionsReturn",{
        "pagination": fields.Nested(pay_pag_model),
        "data": fields.List(fields.Nested(pay_model))
    }
)


@ns_payment.route("/")
class PaymentConditionsList(Resource):
    @ns_payment.response(HTTPStatus.OK,"Obtem a lista de condições de pagamento",pay_return)
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_payment.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_payment.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_payment.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query    = "" if request.args.get("query") is None else request.args.get("query")
        try:
            params = _get_params(str(query))
            trash     = False if not hasattr(params,'trash') else True
            list_all  = False if not hasattr(params,"list_all") else True
            order_by  = "id" if not hasattr(params,"order_by") else params.order_by if params is not None else 'id'
            direction = asc if not hasattr(params,'order') else asc if params is not None and params.order=='ASC' else desc

            filter_search        = None if not hasattr(params,"search") else params.search if params is not None else None
            filter_installments  = None if not hasattr(params,"installments") else params.installments if params is not None else None
            filter_received_days = None if not hasattr(params,"received_days") else params.received_days if params is not None else None
 
            rquery = Select(B2bPaymentConditions.id,
                            B2bPaymentConditions.name,
                            B2bPaymentConditions.installments,
                            B2bPaymentConditions.received_days,
                            B2bPaymentConditions.date_created,
                            B2bPaymentConditions.date_updated)\
                            .where(B2bPaymentConditions.trash==trash)\
                            .order_by(direction(getattr(B2bPaymentConditions,order_by)))
            
            if filter_search is not None:
                rquery = rquery.where(B2bPaymentConditions.name.like("%{}%".format(filter_search)))

            if filter_installments is not None:
                rquery = rquery.where(B2bPaymentConditions.installments==filter_installments)

            if filter_received_days is not None:
                rquery = rquery.where(B2bPaymentConditions.received_days==filter_received_days)

            if not list_all:
                pag    = db.paginate(rquery,page=pag_num,per_page=pag_size)
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
                        "id":m.id,
                        "name": m.name,
                        "received_days": m.received_days,
                        "installments": m.installments,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                    "id":m.id,
                    "name": m.name,
                    "received_days": m.received_days,
                    "installments": m.installments,
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

    @ns_payment.response(HTTPStatus.OK,"Cria uma nova condição de pagamento no sistema")
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Falha ao criar nova condicao de pagamento!")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            payCond = B2bPaymentConditions()
            payCond.name          = req["name"]
            payCond.received_days = req["received_days"]
            payCond.installments  = req["installments"]
            db.session.add(payCond)
            db.session.commit()
            return payCond.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_payment.response(HTTPStatus.OK,"Exclui os dados de uma condição de pagamento")
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                payCond = B2bPaymentConditions.query.get(id)
                setattr(payCond,"trash",True)
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_payment.route("/<int:id>")
@ns_payment.param("id","Id do registro")
class PaymentConditionApi(Resource):
    @ns_payment.response(HTTPStatus.OK,"Obtem um registro de uma condição de pagamento",pay_model)
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            reg:B2bPaymentConditions|None = B2bPaymentConditions.query.get(id)
            if reg is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST

            return {
                "id": reg.id,
                "name": reg.name,
                "received_days": reg.received_days,
                "installments": reg.installments,
                "date_created": reg.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated":  None if reg.date_updated is None else reg.date_updated.strftime("%Y-%m-%d %H:%M:%S"),
                "trash": reg.trash
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_payment.response(HTTPStatus.OK,"Salva dados de uma condição de pgamento")
    @ns_payment.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            payCond:B2bPaymentConditions = B2bPaymentConditions.query.get(id) # type: ignore
            payCond.name          = req["name"]
            payCond.received_days = req["received_days"]
            payCond.installments  = req["installments"]
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }