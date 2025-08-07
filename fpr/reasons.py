from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.tenant import FprReason
from models.helpers import _get_params, db
from sqlalchemy import Select, desc, exc, asc
from flask_restx import Resource, Namespace, fields

ns_reason = Namespace("reasons",description="Operações para manipular dados de motivos de devolução")

#API Models
cou_pag_model = ns_reason.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)
cou_model = ns_reason.model(
    "Reason",{
        "id": fields.Integer,
        "name": fields.String
    }
)

cou_return = ns_reason.model(
    "ReasonReturn",{
        "pagination": fields.Nested(cou_pag_model),
        "data": fields.List(fields.Nested(cou_model))
    }
)

@ns_reason.route("/")
class CategoryList(Resource):
    @ns_reason.response(HTTPStatus.OK,"Obtem a listagem de países",cou_return)
    @ns_reason.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_reason.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_reason.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_reason.param("query","Texto para busca","query")
    @ns_reason.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_reason.param("order_by","Campo de ordenacao","query")
    @ns_reason.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))

        try:
            params    = _get_params(request.args.get("query"))
            direction = asc if not hasattr(params,'order') else asc if params is not None and params.order=='ASC' else desc
            order_by  = 'id' if not hasattr(params,'order_by') else params.order_by if params is not None else 'id'
            search    = None if not hasattr(params,"search") else params.search if params is not None else None
            list_all  = False if not hasattr(params,"list_all") else params.list_all if params is not None else False
            trash     = False if not hasattr(params,"trash") else True

            rquery = Select(FprReason.id,
                            FprReason.description,
                            FprReason.date_created,
                            FprReason.date_updated)\
                        .where(FprReason.trash==trash)\
                        .order_by(direction(getattr(FprReason,order_by)))
            
            if search is not None:
                rquery = rquery.where(FprReason.description.like('%{}%'.format(search)))

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
						"description": m.description,
						"date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
						"date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
					} for m in db.session.execute(rquery)]
				}
            else:
                retorno = [{
						"id": m.id,
						"description": m.description,
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

    @ns_reason.response(HTTPStatus.OK,"Cria um novo país")
    @ns_reason.response(HTTPStatus.BAD_REQUEST,"Falha ao criar novo país!")
    @ns_reason.doc(body=cou_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            reg = FprReason()
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
    
    @ns_reason.response(HTTPStatus.OK,"Exclui os dados de um país")
    @ns_reason.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self)->bool|dict:
        try:
            req = request.get_json()
            for id in req["ids"]:
                reg:FprReason|None = FprReason.query.get(id)
                setattr(reg,"trash",req["toTrash"])
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_reason.route("/<int:id>")
class CategoryApi(Resource):
    @ns_reason.response(HTTPStatus.OK,"Obtem um registro de um país",cou_model)
    @ns_reason.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            reason = FprReason.query.get(id)
            if reason is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST
            
            return {
                "id": reason.id,
                "description": reason.description,
                "date_created": reason.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": reason.date_updated.strftime("%Y-%m-%d %H:%M:%S") if reason.date_updated is not None else None
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_reason.response(HTTPStatus.OK,"Atualiza os dados de um país")
    @ns_reason.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int)->bool|dict:
        try:
            req = request.get_json()
            reg:FprReason|None = FprReason.query.get(id)
            setattr(reg,"description",req["description"])
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }