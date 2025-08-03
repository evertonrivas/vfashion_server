from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.public import SysCountries
from models.helpers import _get_params, db
from sqlalchemy import Select, desc, exc, asc
from flask_restx import Resource,Namespace,fields

ns_country = Namespace("countries",description="Operações para manipular dados de países")

#API Models
cou_pag_model = ns_country.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)
cou_model = ns_country.model(
    "Country",{
        "id": fields.Integer,
        "name": fields.String
    }
)

cou_return = ns_country.model(
    "CountryReturn",{
        "pagination": fields.Nested(cou_pag_model),
        "data": fields.List(fields.Nested(cou_model))
    }
)

@ns_country.route("/")
class CategoryList(Resource):
    @ns_country.response(HTTPStatus.OK,"Obtem a listagem de países",cou_return)
    @ns_country.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_country.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_country.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_country.param("query","Texto para busca","query")
    @ns_country.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_country.param("order_by","Campo de ordenacao","query")
    @ns_country.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num   = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size  = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))

        try:
            params = _get_params(request.args.get("query"))
            if params is not None:
                direction = asc if not hasattr(params,'order') else asc if params.order=='ASC' else desc
                order_by  = 'id' if not hasattr(params,'order_by') else params.order_by
                search    = None if not hasattr(params,"search") else params.search
                list_all  = False if not hasattr(params,"list_all") else params.list_all

            rquery = Select(SysCountries.id,
                            SysCountries.name).select_from(SysCountries)\
                            .order_by(direction(getattr(SysCountries,order_by)))

            if search is not None:
                rquery = rquery.where(SysCountries.name.like("%{}%".format(search)))

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
						"name": m.name
					} for m in db.session.execute(rquery)]
				}
            else:
                retorno = [{
						"id": m.id,
						"name": m.name
					} for m in db.session.execute(rquery)]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_country.response(HTTPStatus.OK,"Cria um novo país")
    @ns_country.response(HTTPStatus.BAD_REQUEST,"Falha ao criar novo país!")
    @ns_country.doc(body=cou_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            reg = SysCountries()
            reg.name = req["name"]
            db.session.add(reg)
            db.session.commit()
            return reg.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_country.response(HTTPStatus.OK,"Exclui os dados de um país")
    @ns_country.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                reg = SysCountries.query.get(id)
                setattr(reg,"trash",req["toTrash"])
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_country.route("/<int:id>")
class CategoryApi(Resource):
    @ns_country.response(HTTPStatus.OK,"Obtem um registro de um país",cou_model)
    @ns_country.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            reg:SysCountries|None = SysCountries.query.get(id)
            if reg is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST
            return {
                "id": reg.id,
                "name": reg.name
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_country.response(HTTPStatus.OK,"Atualiza os dados de um país")
    @ns_country.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            reg:SysCountries|None = SysCountries.query.get(id)
            if reg is not None:
                reg.name = req["name"]
                db.session.commit()
                return True
            return False 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_country.response(HTTPStatus.OK,"Exclui os dados de um país")
    @ns_country.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            reg = SysCountries.query.get(id)
            setattr(reg,"trash",True)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }