from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmProductModel,db
import sqlalchemy as sa
from sqlalchemy import exc
from auth import auth

ns_model = Namespace("products-model",description="Operações para manipular dados de modelos de produtos")

model_pag_model = ns_model.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

model_model = ns_model.model(
    "ProductModel",{
        "id": fields.Integer,
        "name": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

model_return = ns_model.model(
    "ProductModelReturn",{
        "pagination": fields.Nested(model_pag_model),
        "data": fields.List(fields.Nested(model_model))
    }
)

@ns_model.route("/")
class CategoryList(Resource):
    @ns_model.response(HTTPStatus.OK.value,"Obtem a listagem de categorias de modelos de produto",model_return)
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_model.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_model.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_model.param("query","Texto para busca","query")
    @ns_model.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    #@auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        list_all = False if request.args.get("list_all") is None else True
        try:
            if search=="":
                rquery = CmmProductModel.query.filter(CmmProductModel.trash==False)
            else:
                rquery = CmmProductModel.query.filter(sa.and_(CmmProductModel.trash==False,CmmProductModel.name.like(search)))

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

    @ns_model.response(HTTPStatus.OK.value,"Cria um novo modelo de produto no sistema")
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo modelo de produto!")
    @ns_model.doc(body=model_model)
    #@auth.login_required
    def post(self):
        try:
            type = CmmProductModel()
            type.name = request.form.get("name")
            db.session.add(type)
            db.session.commit()
            return type.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_model.route("/<int:id>")
class CategoryApi(Resource):
    @ns_model.response(HTTPStatus.OK.value,"Obtem um registro de um modelo de produto",model_model)
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def get(self,id:int):
        try:
            return CmmProductModel.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_model.response(HTTPStatus.OK.value,"Atualiza os dados de um modelo de produto")
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def post(self,id:int):
        try:
            cat = CmmProductModel.query.get(id)
            cat.name = cat.name if request.form.get("name") is None else request.form.get("name")
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_model.response(HTTPStatus.OK.value,"Exclui os dados de um modelo de produto")
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def delete(self,id:int):
        try:
            cat = CmmProductModel.query.get(id)
            cat.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }