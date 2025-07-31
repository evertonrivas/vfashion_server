from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.tenant import CmmMeasureUnit
from models.helpers import _get_params, db
from sqlalchemy import Select, desc, exc, asc
from flask_restx import Resource,Namespace,fields

ns_measure_unit = Namespace("measure-unit",description="Operações para manipular dados de países")

#API Models
mu_pag_model = ns_measure_unit.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)
mu_model = ns_measure_unit.model(
    "MeasureUnit",{
        "id": fields.Integer,
        "name": fields.String
    }
)

mu_return = ns_measure_unit.model(
    "MeasureUnitReturn",{
        "pagination": fields.Nested(mu_pag_model),
        "data": fields.List(fields.Nested(mu_model))
    }
)

@ns_measure_unit.route("/")
class CategoryList(Resource):
    @ns_measure_unit.response(HTTPStatus.OK,"Obtem a listagem de unidades de medida",mu_return)
    @ns_measure_unit.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_measure_unit.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_measure_unit.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_measure_unit.param("query","Texto para busca","query")
    @ns_measure_unit.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_measure_unit.param("order_by","Campo de ordenacao","query")
    @ns_measure_unit.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))

        try:
            params = _get_params(str(request.args.get("query")))
            direction = asc if not hasattr(params,'order') else asc if params is not None and params.order=='ASC' else desc
            order_by  = 'id' if not hasattr(params,'order_by') else params.order_by if params is not None else 'id'
            trash     = False if not hasattr(params,'trash') else True
            search    = None if not hasattr(params,"search") else params.search if params is not None else None
            list_all  = False if not hasattr(params,"list_all") else True

            rquery = Select(CmmMeasureUnit.id,
                            CmmMeasureUnit.code,
                            CmmMeasureUnit.description)\
                            .where(CmmMeasureUnit.trash==trash)\
                            .order_by(direction(getattr(CmmMeasureUnit,order_by)))
            
            if search is not None:
                rquery = rquery.where(CmmMeasureUnit.description.like("%{}%".format("search")))

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
                        "code": m.code,
						"description": m.description
					} for m in db.session.execute(rquery)]
				}
            else:
                retorno = [{
						"id": m.id,
						"code": m.code,
						"description": m.description
					} for m in db.session.execute(rquery)]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_measure_unit.response(HTTPStatus.OK,"Cria uma nova unidade de media")
    @ns_measure_unit.response(HTTPStatus.BAD_REQUEST,"Falha ao criar nova unidade de medida!")
    @ns_measure_unit.doc(body=mu_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            reg = CmmMeasureUnit()
            reg.code        = req["code"]
            reg.description = req["description"]
            db.session.add(reg)
            db.session.commit()
            return reg.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_measure_unit.response(HTTPStatus.OK,"Exclui os dados de unidade(s) de medida")
    @ns_measure_unit.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                reg:CmmMeasureUnit = CmmMeasureUnit.query.get(id) # type: ignore
                reg.trash = req["toTrash"]
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_measure_unit.route("/<int:id>")
class CategoryApi(Resource):
    @ns_measure_unit.response(HTTPStatus.OK,"Obtem um registro de uma unidade de medida",mu_model)
    @ns_measure_unit.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            reg: CmmMeasureUnit|None = CmmMeasureUnit.query.get(id)
            if reg is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST
            return {
                "id": reg.id,
                "code": reg.code,
                "description": reg.description,
                "trash": reg.trash
            }
            return 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_measure_unit.response(HTTPStatus.OK,"Atualiza os dados de uma unidade de medida")
    @ns_measure_unit.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            reg:CmmMeasureUnit = CmmMeasureUnit.query.get(id) # type: ignore
            reg.description = req["description"]
            reg.code        = req["code"]
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }