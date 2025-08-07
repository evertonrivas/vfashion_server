from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from datetime import datetime
from models.tenant import B2bBrand
from models.helpers import _get_params, db
from sqlalchemy import Select, exc, asc, desc
from flask_restx import Resource, Namespace, fields

ns_comission = Namespace("representative-comission",description="Operações para manipular dados de comissões de representantes")

brand_pag_model = ns_comission.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

comission_model = ns_comission.model(
    "Comission",{
        "id": fields.Integer,
        "id_representative": fields.Integer,
        "value": fields.Decimal
    }
)

brand_return = ns_comission.model(
    "ComissionReturn",{
        "pagination": fields.Nested(brand_pag_model),
        "data": fields.List(fields.Nested(comission_model))
    }
)

@ns_comission.route("/")
class ComissionList(Resource):
    @ns_comission.response(HTTPStatus.OK,"Obtem um registro de comissões",brand_return)
    @ns_comission.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @ns_comission.param("page","Número da página de registros","query",type=int,required=True)
    @ns_comission.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_comission.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query    = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params    = _get_params(query)
            if params is None:
                return None
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

            if list_all:
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
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id":m.id,
                        "name":m.name,
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

    @ns_comission.response(HTTPStatus.OK,"Cria uma nova coleção")
    @ns_comission.response(HTTPStatus.BAD_REQUEST,"Falha ao criar registro!")
    @ns_comission.doc(body=comission_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()

            brand= B2bBrand()
            brand.name = req["name"]
            setattr(brand,"date_created",datetime.now())
            db.session.add(brand)
            db.session.commit()

            return brand.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
        
    @ns_comission.response(HTTPStatus.OK,"Exclui os dados de uma ou mais marcas")
    @ns_comission.response(HTTPStatus.BAD_REQUEST,"Falha ao excluir registro!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                brand:B2bBrand|None = B2bBrand.query.get(id)
                setattr(brand,"trash",(req["toTrash"]))
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_comission.route("/<int:id>")
@ns_comission.param("id","Id do registro")
class CollectionApi(Resource):
    @ns_comission.response(HTTPStatus.OK,"Retorna os dados dados de uma coleção")
    @ns_comission.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            cquery = B2bBrand.query.get(id)
            if cquery is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST

            return {
                "id": cquery.id,
                "name": cquery.name,
                "date_created": cquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": cquery.date_updated.strftime("%Y-%m-%d %H:%M:%S") if cquery.date_updated is not None else None
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_comission.response(HTTPStatus.OK,"Atualiza os dados de uma marca")
    @ns_comission.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @ns_comission.doc(body=comission_model)
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            brand:B2bBrand|None = B2bBrand.query.get(id)
            setattr(brand,"name",req["name"])
            setattr(brand,"date_updated",datetime.now())
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }