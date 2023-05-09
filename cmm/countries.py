from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmCountry,db
from sqlalchemy import desc, exc, asc
from auth import auth
from config import Config

ns_country = Namespace("coutries",description="Operações para manipular dados de países")

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
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        list_all = False if request.args.get("list_all") is None else True
        order_by   = "id" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc

        try:
            if search=="":
                rquery = CmmCountry\
                    .query\
                    .order_by(direction(getattr(CmmCountry, order_by)))
            else:
                rquery = CmmCountry\
                    .query\
                    .filter(CmmCountry.name.like(search))\
                    .order_by(direction(getattr(CmmCountry, order_by)))

            if list_all==False:
                rquery = rquery.paginate(page=pag_num,per_page=pag_size)
                retorno = {
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
            else:
                retorno = [{
						"id": m.id,
						"name": m.name,
						"date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
						"date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
					} for m in rquery]
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
            reg = CmmCountry()
            reg.name = request.form.get("name")
            db.session.add(reg)
            db.session.commit()
            return reg.id
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
            return CmmCountry.query.get(id).to_dict()
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
            reg = CmmCountry.query.get(id)
            reg.name = reg.name if req["name"] is None else req["name"]
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
            reg = CmmCountry.query.get(id)
            reg.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }