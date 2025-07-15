from auth import auth
# from os import environ
# from flask import request
from http import HTTPStatus
# from models.helpers import _get_params, db
from flask_restx import Resource, Namespace, fields
# from sqlalchemy import exc, Select, and_, Delete, asc, desc

ns_invoice = Namespace("invoices",description="Operações para manipular dados de notas fiscais")

inv_pag_model = ns_invoice.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

invoice_model = ns_invoice.model(
    "Invoice",{
    
    }
)

inv_return = ns_invoice.model(
    "OrderReturn",{
        "pagination": fields.Nested(inv_pag_model),
        "data": fields.List(fields.Nested(invoice_model))
    }
)

@ns_invoice.route("/")
class InvoiceList(Resource):
    @ns_invoice.response(HTTPStatus.OK,"Obtem a listagem de produto",inv_return)
    @ns_invoice.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_invoice.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_invoice.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_invoice.param("query","Texto para busca","query")
    @ns_invoice.param("order_by","Campo de ordenacao","query")
    @ns_invoice.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        # pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        # pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        # query    = "" if request.args.get("query") is None else request.args.get("query")
        pass


    def post(self):
        pass

@ns_invoice.route("/<int:id>")
class InvoiceAPI(Resource):
    def get(self,id:int):
        pass

    def post(self,id:int):
        pass

    def delete(self,id:int):
        pass