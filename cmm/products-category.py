from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmCategory,db
import sqlalchemy as sa
from sqlalchemy import exc
from auth import auth

ns_cat  = Namespace("products-category",description="Operações para manipular dados de categorias de produtos")

cat_pag_model = ns_cat.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

cat_model = ns_cat.model(
    "Category",{
        "id": fields.Integer,
        "name": fields.String,
        "id_parent": fields.Integer,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
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
    @ns_cat.response(HTTPStatus.OK.value,"Obtem a listagem de categorias de produto",cat_return)
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_cat.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_cat.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_cat.param("query","Texto para busca","query")
    @ns_cat.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        list_all = False if request.args.get("list_all") is None else True
        try:
            if search=="":
                    rquery = CmmCategory.query.filter(CmmCategory.trash==False)
            else:
                rquery = CmmCategory.query.filter(sa.and_(CmmCategory.trash==False,CmmCategory.name.like(search)))

            if list_all==False:
                rquery = rquery.paginate(page=pag_num,per_page=pag_size)
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
                    "name": m.name,
                    "id_parent": m.id_parent,
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

    @ns_cat.response(HTTPStatus.OK.value,"Cria uma nova categoria de produto no sistema")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova categoria de produto!")
    @ns_cat.doc(body=cat_model)
    @auth.login_required
    def post(self):
        try:
            cat = CmmCategory()
            cat.name = request.form.get("name")
            cat.id_parent = int(request.form.get("id_parent")) if request.form.get("id_parent")!=None else None
            db.session.add(cat)
            db.session.commit()
            return cat.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_cat.route("/<int:id>")
class CategoryApi(Resource):
    @ns_cat.response(HTTPStatus.OK.value,"Obtem um registro de uma categoria",cat_model)
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmCategory.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_cat.response(HTTPStatus.OK.value,"Atualiza os dados de uma categoria")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            cat = CmmCategory.query.get(id)
            cat.name      = cat.name if request.form.get("name") is None else request.form.get("name")
            cat.id_parent = cat.id_parent if request.form.get("id_parent") is None else int(request.form.get("id_parent"))
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_cat.response(HTTPStatus.OK.value,"Exclui os dados de uma categoria")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            cat = CmmCategory.query.get(id)
            cat.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }