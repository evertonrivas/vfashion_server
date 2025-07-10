from datetime import datetime
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models.public import B2bBrand, _get_params, db
from sqlalchemy import Select, exc, asc, desc
from auth import auth
from os import environ

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
    @ns_comission.response(HTTPStatus.OK.value,"Obtem um registro de comissões",brand_return)
    @ns_comission.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_comission.param("page","Número da página de registros","query",type=int,required=True)
    @ns_comission.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_comission.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params    = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            trash     = False if hasattr(params,'trash')==False else True
            list_all  = False if hasattr(params,'list_all')==False else True

            rquery = Select(B2bBrand.id,
                            B2bBrand.name,
                            B2bBrand.date_created,
                            B2bBrand.date_updated)\
                            .where(B2bBrand.trash==trash)\
                            .order_by(direction(getattr(B2bBrand,order_by)))
            
            if search is not None:
                rquery = rquery.where(B2bBrand.name.like("%{}%".format(search)))

            if list_all==False:
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

    @ns_comission.response(HTTPStatus.OK.value,"Cria uma nova coleção")
    @ns_comission.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_comission.doc(body=comission_model)
    @auth.login_required
    def post(self)->int|dict:
        try:
            req = request.get_json()

            brand = B2bBrand()
            brand.name = req["name"]
            brand.date_created = datetime.now()
            db.session.add(brand)
            db.session.commit()

            return brand.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
        
    @ns_comission.response(HTTPStatus.OK.value,"Exclui os dados de uma ou mais marcas")
    @ns_comission.response(HTTPStatus.BAD_REQUEST.value,"Falha ao excluir registro!")
    @auth.login_required
    def delete(self)->bool|dict:
        try:
            req = request.get_json()
            for id in req["ids"]:
                brand = B2bBrand.query.get(id)
                brand.trash = req["toTrash"]
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
    @ns_comission.response(HTTPStatus.OK.value,"Retorna os dados dados de uma coleção")
    @ns_comission.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            cquery = B2bBrand.query.get(id)

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
    
    @ns_comission.response(HTTPStatus.OK.value,"Atualiza os dados de uma marca")
    @ns_comission.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_comission.doc(body=comission_model)
    @auth.login_required
    def post(self,id:int)->bool|dict:
        try:
            req = request.get_json()
            brand = B2bBrand.query.get(id)
            brand.name  = req["name"]
            brand.date_updated = datetime.now()
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }