from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.helpers import _get_params, db
from models.tenant import CmmProductsModels
from sqlalchemy import Select, exc, desc, asc
from flask_restx import Resource,Namespace,fields

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
class ModelList(Resource):
    @ns_model.response(HTTPStatus.OK,"Obtem a listagem de categorias de modelos de produto",model_return)
    @ns_model.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_model.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_model.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_model.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query    = "" if request.args.get("query") is None else request.args.get("query")
        try:
            params = _get_params(query)
            direction = asc if not hasattr(params,'order') else asc if params is not None and params.order=='ASC' else desc
            order_by  = 'id' if not hasattr(params,'order_by') else params.order_by if params is not None else 'id'
            search    = None if not hasattr(params,"search") else params.search if params is not None else None
            trash     = False if not hasattr(params,'trash') else True
            list_all  = False if not hasattr(params,'list_all') else True

            rquery = Select(CmmProductsModels.id,
                            CmmProductsModels.origin_id,
                            CmmProductsModels.name,
                            CmmProductsModels.date_created,
                            CmmProductsModels.date_updated)\
                            .where(CmmProductsModels.trash==trash)\
                            .order_by(direction(getattr(CmmProductsModels,order_by)))

            if search is not None:
                rquery = rquery.where(CmmProductsModels.name.like("%{}%".format(search)))

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
                        "id": m.id,
                        "origin_id":m.origin_id,
                        "name": m.name,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id": m.id,
                        "origin_id": m.origin_id,
                        "name": m.name,
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

    @ns_model.response(HTTPStatus.OK,"Cria um novo modelo de produto no sistema")
    @ns_model.response(HTTPStatus.BAD_REQUEST,"Falha ao criar novo modelo de produto!")
    @ns_model.doc(body=model_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            type = CmmProductsModels()
            type.name = req["name"]
            setattr(type,"origin_id",(None if "origin_id" not in req else req['origin_id']))
            db.session.add(type)
            db.session.commit()
            return type.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_model.response(HTTPStatus.OK,"Exclui os dados de um modelo de produto")
    @ns_model.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                cat = CmmProductsModels.query.get(id)
                setattr(cat,"trash",req["toTrash"])
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_model.route("/<int:id>")
class ModelApi(Resource):
    @ns_model.response(HTTPStatus.OK,"Obtem um registro de um modelo de produto",model_model)
    @ns_model.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            reg:CmmProductsModels|None = CmmProductsModels.query.get(id)
            if reg is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST
            return {
                "id": reg.id,
                "origin_id": reg.origin_id,
                "name": reg.name,
                "date_created": reg.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": None if reg.date_updated is None else reg.date_updated.strftime("%Y-%m-%d %H:%M:%S"),
                "trash": reg.trash
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_model.response(HTTPStatus.OK,"Atualiza os dados de um modelo de produto")
    @ns_model.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            cat = CmmProductsModels.query.get(id)
            setattr(cat,"name",req["name"])
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }