from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmCategory,CmmProductType,CmmProductModel,db
import sqlalchemy as sa
from sqlalchemy import exc
from auth import auth

ns_cat  = Namespace("products-category",description="Operações para manipular dados de categorias de produtos")
ns_type = Namespace("products-type",description="Operações para manipular dados de tipos de produtos")

cat_pag_model = ns_cat.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

cat_prd_model = ns_cat.model(
    "ProductCategory",{
        "id": fields.Integer
    }
)

cat_model = ns_cat.model(
    "Category",{
        "id": fields.Integer,
        "name": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime,
        "products": fields.List(fields.Nested(cat_prd_model))
    }
)

cat_return = ns_cat.model(
    "CategoryReturn",{
        "pagination": fields.Nested(cat_pag_model),
        "data": fields.List(fields.Nested(cat_model))
    }
)

@ns_cat.route("/")
class CategoryList(Resource):
    @ns_cat.response(HTTPStatus.OK.value,"Obtem a listagem de produto",cat_return)
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_cat.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_cat.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_cat.param("query","Texto para busca","query")
    #@auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        try:
            rquery = ""
        except exc.DatabaseError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_cat.response(HTTPStatus.OK.value,"Cria um novo produto no sistema")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo produto!")
    @ns_cat.doc(body=cat_model)
    #@auth.login_required
    def post(self):
        return None

@ns_cat.route("/<int:id>")
class CategoryApi(Resource):
    @ns_cat.response(HTTPStatus.OK.value,"Obtem um registro de uma categoria",cat_model)
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def get(self,id:int):
        pass

    @ns_cat.response(HTTPStatus.OK.value,"Atualiza os dados de uma categoria")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def post(self,id:int):
        pass

    @ns_cat.response(HTTPStatus.OK.value,"Exclui os dados de uma categoria")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def delete(self,id:int):
        pass