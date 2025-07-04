from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmCountries, _get_params, db
# from models import _show_query
from sqlalchemy import Select, desc, exc, asc
from auth import auth
from os import environ

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
    @ns_country.response(HTTPStatus.OK.value,"Obtem a listagem de países",cou_return)
    @ns_country.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_country.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_country.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_country.param("query","Texto para busca","query")
    @ns_country.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_country.param("order_by","Campo de ordenacao","query")
    @ns_country.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num   = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))

        try:
            params = _get_params(request.args.get("query"))
            direction = asc if hasattr(params,'order')==False else asc if params.order=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search = None if hasattr(params,"search")==False else params.search
            list_all = False if hasattr(params,"list_all")==False else params.list_all

            rquery = Select(CmmCountries.id,
                            CmmCountries.name).select_from(CmmCountries)\
                            .order_by(direction(getattr(CmmCountries,order_by)))

            if search is not None:
                rquery = rquery.where(CmmCountries.name.like("%{}%".format(search)))

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

    @ns_country.response(HTTPStatus.OK.value,"Cria um novo país")
    @ns_country.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo país!")
    @ns_country.doc(body=cou_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            reg = CmmCountries()
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
        
    @ns_country.response(HTTPStatus.OK.value,"Exclui os dados de um país")
    @ns_country.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                reg = CmmCountries.query.get(id)
                reg.trash = req["toTrash"]
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
    @ns_country.response(HTTPStatus.OK.value,"Obtem um registro de um país",cou_model)
    @ns_country.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmCountries.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_country.response(HTTPStatus.OK.value,"Atualiza os dados de um país")
    @ns_country.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            reg = CmmCountries.query.get(id)
            reg.name = req["name"]
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_country.response(HTTPStatus.OK.value,"Exclui os dados de um país")
    @ns_country.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            reg = CmmCountries.query.get(id)
            reg.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }