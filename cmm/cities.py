from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.helpers import db
# from models import _show_query
from sqlalchemy import Select, desc, exc, asc
from flask_restx import Resource,Namespace,fields
from models.tenant import CmmCities, CmmCountries, CmmStateRegions, _get_params

ns_city = Namespace("cities",description="Operações para manipular dados de cidades")

#API Models
cou_pag_model = ns_city.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)
cou_model = ns_city.model(
    "City",{
        "id": fields.Integer,
        "name": fields.String
    }
)

cou_return = ns_city.model(
    "CityReturn",{
        "pagination": fields.Nested(cou_pag_model),
        "data": fields.List(fields.Nested(cou_model))
    }
)

@ns_city.route("/")
class CitiesList(Resource):
    @ns_city.response(HTTPStatus.OK.value,"Obtem a listagem de cidades",cou_return)
    @ns_city.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_city.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_city.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_city.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query    = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params = _get_params(str(query))
            if params is not None:
                direction = asc if not hasattr(params,'order') else asc if params.order=='ASC' else desc
                order_by  = 'id' if not hasattr(params,'order_by') else params.order_by
                search = None if not hasattr(params,"search") else params.search
                list_all = False if not hasattr(params,"list_all") else params.list_all
                filter_state = None if not hasattr(params,"state_region") else params.state_region

            rquery = Select(CmmCities.id,
                   CmmCities.name,
                   CmmStateRegions.id.label("state_region_id"),
                   CmmStateRegions.name.label("state_region_name"),
                   CmmStateRegions.acronym,
                   CmmCountries.id.label("country_id"),
                   CmmCountries.name.label("country_name"))\
                   .join(CmmStateRegions,CmmStateRegions.id==CmmCities.id_state_region)\
                   .join(CmmCountries,CmmCountries.id==CmmStateRegions.id_country)\
                   .order_by(direction(getattr(CmmCities,order_by)))
            
            if search is not None and search!="":
                rquery = rquery.where(
                    CmmCities.name.like('%{}%'.format(search)) |
                    CmmStateRegions.name.like('%{}%'.format(search)) |
                    CmmCountries.name.like('%{}%'.format(search))
                )

            if filter_state is not None:
                if str(filter_state).find(",")==-1:
                    rquery = rquery.where(CmmCities.id_state_region==filter_state)
                else:
                    rquery = rquery.where(CmmCities.id_state_region.in_(filter_state))

            #print(rquery)

            if not list_all:
                pag = db.paginate(rquery,page=pag_num,per_page=pag_size)
                rquery = rquery.limit(pag_size).offset((pag_num -1)*pag_size)
                return {
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
                        "state_region":{
                            "id": m.state_region_id,
                            "name": m.state_region_name,
                            "acronym": m.acronym,
                            "country": {
                                "id": m.country_id,
                                "name": m.country_name
                            }
                        }
                    }for m in db.session.execute(rquery)]
                }
            else:
                return [{
                        "id": m.id,
                        "name": m.name,
                        "state_region":{
                            "id": m.state_region_id,
                            "name": m.state_region_name,
                            "acronym":m.acronym,
                            "country": {
                                "id": m.country_id,
                                "name": m.country_name
                            }
                        }
                    }for m in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_city.response(HTTPStatus.OK.value,"Cria uma nova cidade")
    @ns_city.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo registro!")
    @ns_city.doc(body=cou_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            reg:CmmCities = CmmCities()
            reg.name = req["name"]
            reg.id_state_region = req["id_state_region"]
            db.session.add(reg)
            db.session.commit()
            return reg.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_city.route("/<int:id>")
class CityApi(Resource):
    @ns_city.response(HTTPStatus.OK.value,"Obtem um registro de uma nova cidade",cou_model)
    @ns_city.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            req:CmmCities|None = CmmCities.query.get(id)
            if req is not None:
                return {
                    "id": req.id,
                    "id_state_region": req.id_state_region,
                    "name": req.name,
                    "brazil_ibge_code" : req.brazil_ibge_code
                }
            return None
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_city.response(HTTPStatus.OK.value,"Atualiza os dados de uma cidade")
    @ns_city.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            reg:CmmCities|None = CmmCities.query.get(id)
            if reg is not None:
                reg.name = req["name"]
                reg.id_state_region = req["id_state_region"]
                db.session.commit()
                return True
            return False 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_city.response(HTTPStatus.OK.value,"Exclui os dados de uma cidade")
    @ns_city.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            reg = CmmCities.query.get(id)
            setattr(reg,"trash",True)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }