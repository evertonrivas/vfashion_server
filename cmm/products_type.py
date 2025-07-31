from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.helpers import _get_params, db
from models.tenant import CmmProductsTypes
from sqlalchemy import Select, exc, asc, desc
from flask_restx import Resource,Namespace,fields

ns_type = Namespace("products-type",description="Operações para manipular dados de tipos de produtos")

type_pag_model = ns_type.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

type_model = ns_type.model(
    "ProductType",{
        "id": fields.Integer,
        "name": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

type_return = ns_type.model(
    "ProductTypeReturn",{
        "pagination": fields.Nested(type_pag_model),
        "data": fields.List(fields.Nested(type_model))
    }
)

@ns_type.route("/")
class CategoryList(Resource):
    @ns_type.response(HTTPStatus.OK,"Obtem a listagem de categorias de tipos de produto",type_return)
    @ns_type.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_type.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_type.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_type.param("query","Texto para busca","query")
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

            rquery = Select(CmmProductsTypes.id,
                            CmmProductsTypes.origin_id,
                            CmmProductsTypes.name,
                            CmmProductsTypes.date_created,
                            CmmProductsTypes.date_updated)\
                            .where(CmmProductsTypes.trash==trash)\
                            .order_by(direction(getattr(CmmProductsTypes,order_by)))

            if search is not None:
                rquery = rquery.where(CmmProductsTypes.name.like("%{}%".format(search)))

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
                        "origin_id":m.origin_id,
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

    @ns_type.response(HTTPStatus.OK,"Cria um novo tipo de produto no sistema")
    @ns_type.response(HTTPStatus.BAD_REQUEST,"Falha ao criar novo tipo de produto!")
    @ns_type.doc(body=type_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            type = CmmProductsTypes()
            type.name = req["name"]
            db.session.add(type)
            db.session.commit()
            return type.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_type.response(HTTPStatus.OK,"Exclui os dados de um tipo de produto")
    @ns_type.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                cat = CmmProductsTypes.query.get(id)
                setattr(cat,"trash",req["toTrash"])
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_type.route("/<int:id>")
class CategoryApi(Resource):
    @ns_type.response(HTTPStatus.OK,"Obtem um registro de um tipo de produto",type_model)
    @ns_type.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            reg:CmmProductsTypes|None = CmmProductsTypes.query.get(id)
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
            

    @ns_type.response(HTTPStatus.OK,"Atualiza os dados de um tipo de produto")
    @ns_type.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            cat = CmmProductsTypes.query.get(id)
            setattr(cat,"name",req["name"])
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }