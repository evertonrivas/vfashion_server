from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmStateRegions, _get_params,db
from sqlalchemy import Select, desc, exc, asc, or_
from auth import auth
from config import Config

ns_state_region = Namespace("state-regions",description="Operações para manipular dados de estados ou regiões")

#API Models
cou_pag_model = ns_state_region.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)
cou_model = ns_state_region.model(
    "City",{
        "id": fields.Integer,
        "name": fields.String
    }
)

cou_return = ns_state_region.model(
    "CityReturn",{
        "pagination": fields.Nested(cou_pag_model),
        "data": fields.List(fields.Nested(cou_model))
    }
)

@ns_state_region.route("/")
class CategoryList(Resource):
    @ns_state_region.response(HTTPStatus.OK.value,"Obtem a listagem de cidades",cou_return)
    @ns_state_region.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_state_region.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_state_region.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_state_region.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))

        try:
            params    = _get_params(request.args.get("query"))
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            list_all  = False if hasattr(params,"list_all")==False else params.list_all

            rquery = Select(CmmStateRegions.id,
                            CmmStateRegions.id_country,
                            CmmStateRegions.name,
                            CmmStateRegions.acronym)\
                            .select_from(CmmStateRegions)\
                            .order_by(direction(getattr(CmmStateRegions,order_by)))
            
            if search is not None:
                rquery = rquery.where(or_(
                    CmmStateRegions.name.like("%{}%".format(search)),
                    CmmStateRegions.acronym.like("%{}%".format(search))
                ))

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
                        "id_country": m.id_country,
						"name": m.name,
                        "acronym": m.acronym
					} for m in db.session.execute(rquery)]
				}
            else:
                retorno = [{
						"id": m.id,
                        "id_country": m.id_country,
						"name": m.name,
                        "acronym": m.acronym
					} for m in db.session.execute(rquery)]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_state_region.response(HTTPStatus.OK.value,"Cria uma nova cidade")
    @ns_state_region.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo registro!")
    @ns_state_region.doc(body=cou_model)
    @auth.login_required
    def post(self):
        try:
            reg = CmmStateRegions()
            reg.name = request.form.get("name")
            reg.id_country = request.form.get("id_country")
            db.session.add(reg)
            db.session.commit()
            return reg.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_state_region.route("/<int:id>")
class CategoryApi(Resource):
    @ns_state_region.response(HTTPStatus.OK.value,"Obtem um registro de uma nova cidade",cou_model)
    @ns_state_region.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmStateRegions.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_state_region.response(HTTPStatus.OK.value,"Atualiza os dados de uma cidade")
    @ns_state_region.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            reg = CmmStateRegions.query.get(id)
            reg.name = reg.name if req["name"] is None else req["name"]
            reg.id_country = reg.id_country if req["id_country"] is None else req["id_country"]
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_state_region.response(HTTPStatus.OK.value,"Exclui os dados de uma cidade")
    @ns_state_region.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            reg = CmmStateRegions.query.get(id)
            reg.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }