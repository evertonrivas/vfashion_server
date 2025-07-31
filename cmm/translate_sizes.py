from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.helpers import _get_params, db
from models.tenant import CmmTranslateSizes
from sqlalchemy import Select, exc, desc, asc
from flask_restx import Resource,Namespace,fields

ns_size = Namespace("translate-sizes",description="Operações para manipular dados de tamanhos")

size_pag_model = ns_size.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

size_model = ns_size.model(
    "TranslateSize",{
        "id": fields.Integer,
        "size_name": fields.String,
        "size": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

size_return = ns_size.model(
    "TranslateSizeReturn",{
        "pagination": fields.Nested(size_pag_model),
        "data": fields.List(fields.Nested(size_model))
    }
)

@ns_size.route("/")
class CategoryList(Resource):
    @ns_size.response(HTTPStatus.OK,"Obtem a listagem de traduções de tamanhos",size_return)
    @ns_size.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_size.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_size.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_size.param("query","Texto para busca","query")
    @ns_size.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_size.param("order_by","Campo de ordenacao","query")
    @ns_size.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query    = "" if request.args.get("query") is None else request.args.get("query")
        try:
            params = _get_params(query)
            direction = asc if not hasattr(params,'order') else asc if params is not None and params.order=='ASC' else desc
            order_by  = 'id' if not hasattr(params,'order_by') else params.order_by if params is not None else 'id'
            search    = None if not hasattr(params,"search") else params.search if params is not None else None
            trash     = False if not hasattr(params,'trash') else True
            list_all  = False if not hasattr(params,'list_all') else True

            rquery = Select(CmmTranslateSizes.id,
                            CmmTranslateSizes.new_size,
                            CmmTranslateSizes.name,
                            CmmTranslateSizes.old_size,
                            CmmTranslateSizes.date_created,
                            CmmTranslateSizes.date_updated)\
                            .where(CmmTranslateSizes.trash==trash)\
                            .order_by(direction(getattr(CmmTranslateSizes,order_by)))

            if search is not None:
                rquery = rquery.where(CmmTranslateSizes.new_size.like("%{}%".format(search)))

            # print(params)
            # _show_query(rquery)

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
                        "new_size": m.new_size,
                        "old_size": m.old_size,
                        "name":m.name,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id": m.id,
                        "new_size": m.new_size,
                        "old_size": m.old_size,
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

    @ns_size.response(HTTPStatus.OK,"Cria uma nova tradução de tamanho")
    @ns_size.response(HTTPStatus.BAD_REQUEST,"Falha ao criar novo modelo de produto!")
    @ns_size.doc(body=size_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            for size in req:
                sz = CmmTranslateSizes()
                sz.name = size["name"]
                sz.old_size = size["old_size"]
                sz.new_size = size["new_size"]
                setattr(sz,"trash",False)
                db.session.add(sz)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_size.response(HTTPStatus.OK,"Exclui os dados de uma nova tradução de tamanho")
    @ns_size.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                cor = CmmTranslateSizes.query.get(id)
                setattr(cor,"trash",req["toTrash"])
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_size.route("/<int:id>")
class CategoryApi(Resource):
    @ns_size.response(HTTPStatus.OK,"Obtem um registro de uma nova tradução de tamanho",size_model)
    @ns_size.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            reg:CmmTranslateSizes|None = CmmTranslateSizes.query.get(id)
            if reg is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST
            
            return {
                "id": reg.id,
                "new_size": reg.new_size,
                "name": reg.name,
                "old_size": reg.old_size,
                "trash": reg.trash,
                "date_created": reg.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": None if reg.date_updated is None else reg.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_size.response(HTTPStatus.OK,"Atualiza os dados de uma nova tradução de tamanho")
    @ns_size.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required      
    def post(self,id:int):
        try:
            req = request.get_json()
            if id==0:
                sz          = CmmTranslateSizes()
                sz.name     = req["name"]
                sz.old_size = req["old_size"]
                sz.new_size = req["new_size"]
                db.session.add(sz)
                db.session.commit()
                return sz.id
            else:
                sz:CmmTranslateSizes|None = CmmTranslateSizes.query.get(id)
                if sz is not None:
                    sz.name     = req["name"]
                    sz.old_size = req["old_size"]
                    sz.new_size = req["new_size"]
                    db.session.commit()
                    return True
                return False
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }