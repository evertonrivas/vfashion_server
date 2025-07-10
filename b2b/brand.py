from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.helpers import db
from datetime import datetime
# from models import _show_query
from sqlalchemy import Select, exc, asc, desc
from models.tenant import B2bBrand, _get_params
from flask_restx import Resource,Namespace,fields

ns_brand = Namespace("brand",description="Operações para manipular dados de marcas")

brand_pag_model = ns_brand.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

brand_model = ns_brand.model(
    "Brand",{
        "id": fields.Integer,
        "name": fields.String
    }
)

brand_return = ns_brand.model(
    "BrandReturn",{
        "pagination": fields.Nested(brand_pag_model),
        "data": fields.List(fields.Nested(brand_model))
    }
)

@ns_brand.route("/")
class CollectionList(Resource):
    @ns_brand.response(HTTPStatus.OK.value,"Obtem um registro de uma marca",brand_return)
    @ns_brand.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_brand.param("page","Número da página de registros","query",type=int,required=True)
    @ns_brand.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_brand.param("query","Texto para busca","query")
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
                trash     = False if not hasattr(params,'trash') else True
                list_all  = False if not hasattr(params,'list_all') else True

            rquery = Select(B2bBrand.id,
                            B2bBrand.name,
                            B2bBrand.date_created,
                            B2bBrand.date_updated)\
                            .where(B2bBrand.trash==trash)\
                            .order_by(direction(getattr(B2bBrand,order_by)))
            
            if search is not None:
                rquery = rquery.where(B2bBrand.name.like("%{}%".format(search)))

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
                        "name": m.name,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id":m.id,
                        "name":m.name,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_brand.response(HTTPStatus.OK.value,"Cria uma nova marca")
    @ns_brand.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_brand.doc(body=brand_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()

            brand:B2bBrand = B2bBrand()
            brand.name = req["name"]
            brand.date_created = datetime.now() # type: ignore
            db.session.add(brand)
            db.session.commit()

            return brand.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
        
    @ns_brand.response(HTTPStatus.OK.value,"Exclui os dados de uma ou mais marcas")
    @ns_brand.response(HTTPStatus.BAD_REQUEST.value,"Falha ao excluir registro!")
    @auth.login_required
    def delete(self)->bool|dict:
        try:
            req = request.get_json()
            for id in req["ids"]:
                brand:B2bBrand = B2bBrand.query.get(id) # type: ignore
                brand.trash = req["toTrash"]
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_brand.route("/<int:id>")
@ns_brand.param("id","Id do registro")
class CollectionApi(Resource):
    @ns_brand.response(HTTPStatus.OK.value,"Retorna os dados dados de uma marca")
    @ns_brand.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            cquery:B2bBrand = B2bBrand.query.get(id) # type: ignore

            return {
                "id": cquery.id,
                "name": cquery.name,
                "date_created": cquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": cquery.date_updated.strftime("%Y-%m-%d %H:%M:%S") if cquery.date_updated!=None else None
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_brand.response(HTTPStatus.OK.value,"Atualiza os dados de uma marca")
    @ns_brand.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_brand.doc(body=brand_model)
    @auth.login_required
    def post(self,id:int)->bool|dict:
        try:
            req = request.get_json()
            brand:B2bBrand = B2bBrand.query.get(id) # type: ignore
            brand.name  = req["name"]
            brand.date_updated = datetime.now()  # type: ignore
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }