from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmProductsModels, _get_params,db
from sqlalchemy import Select, exc, and_,desc,asc
from auth import auth
from config import Config

ns_model = Namespace("products-model",description="Operações para manipular dados de modelos de produtos")

model_pag_model = ns_model.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

model_model = ns_model.model(
    "ProductModel",{
        "id": fields.Integer,
        "name": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

model_return = ns_model.model(
    "ProductModelReturn",{
        "pagination": fields.Nested(model_pag_model),
        "data": fields.List(fields.Nested(model_model))
    }
)

@ns_model.route("/")
class CategoryList(Resource):
    @ns_model.response(HTTPStatus.OK.value,"Obtem a listagem de categorias de modelos de produto",model_return)
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_model.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_model.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_model.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else request.args.get("query")
        try:
            params = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            trash     = False if hasattr(params,'trash')==False else True
            list_all  = False if hasattr(params,'list_all')==False else True

            rquery = Select(CmmProductsModels.id,
                            CmmProductsModels.origin_id,
                            CmmProductsModels.name,
                            CmmProductsModels.date_created,
                            CmmProductsModels.date_updated)\
                            .where(CmmProductsModels.trash==trash)\
                            .order_by(direction(getattr(CmmProductsModels,order_by)))

            if search is not None:
                rquery = rquery.where(CmmProductsModels.name.like("%{}%".format(search)))

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
                        "origin_id":m.origin_id,
                        "name": m.name,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id": m.id,
                        "origin_id": m.origin_id,
                        "name": m.name,
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

    @ns_model.response(HTTPStatus.OK.value,"Cria um novo modelo de produto no sistema")
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo modelo de produto!")
    @ns_model.doc(body=model_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            type = CmmProductsModels()
            type.name = req["name"]
            type.origin_id = None if not "origin_id" in req else req['origin_id']
            db.session.add(type)
            db.session.commit()
            return type.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_model.response(HTTPStatus.OK.value,"Exclui os dados de um modelo de produto")
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self)->bool:
        try:
            req = request.get_json()
            for id in req["ids"]:
                cat = CmmProductsModels.query.get(id)
                cat.trash = req["toTrash"]
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_model.route("/<int:id>")
class CategoryApi(Resource):
    @ns_model.response(HTTPStatus.OK.value,"Obtem um registro de um modelo de produto",model_model)
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmProductsModels.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_model.response(HTTPStatus.OK.value,"Atualiza os dados de um modelo de produto")
    @ns_model.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            cat = CmmProductsModels.query.get(id)
            cat.name = cat.name if request.form.get("name") is None else request.form.get("name")
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }