from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmCategories, CmmCategories, _get_params,db
from sqlalchemy import Select, exc,and_,asc,desc
from auth import auth
from config import Config

ns_cat  = Namespace("products-category",description="Operações para manipular dados de categorias de produtos")

cat_pag_model = ns_cat.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

cat_model = ns_cat.model(
    "Category",{
        "id": fields.Integer,
        "name": fields.String,
        "id_parent": fields.Integer,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

cat_return = ns_cat.model(
    "CategoryReturn",{
        "pagination": fields.Nested(cat_pag_model),
        "data": fields.List(fields.Nested(cat_model))
    }
)

@ns_cat.route("/")
class CategoryList(Resource):
    @ns_cat.response(HTTPStatus.OK.value,"Obtem a listagem de categorias de produto",cat_return)
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_cat.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_cat.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_cat.param("query","Texto para busca","query")
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

            filter_just_parent = None if hasattr(params,'just_parent')==False else True
            filter_just_child  = None if hasattr(params,"just_child")==False else True
            
            rquery = Select(CmmCategories.id,
                            CmmCategories.origin_id,
                            CmmCategories.id_parent,
                            CmmCategories.name,
                            CmmCategories.date_created,
                            CmmCategories.date_updated)\
                            .where(CmmCategories.trash==trash)\
                            .order_by(direction(getattr(CmmCategories,order_by)))

            if search is not None:
                rquery = rquery.where(CmmCategories.name.like("%{}%".format(search)))

            if filter_just_parent==True:
                rquery = rquery.where(CmmCategories.id_parent.is_(None))

            if filter_just_child==True:
                rquery = rquery.where(CmmCategories.id_parent.is_not(None))

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
                        "orign_id": m.origin_id,
						"name": m.name,
						"id_parent": m.id_parent,
						"date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
						"date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
					} for m in db.session.execute(rquery)]
				}
            else:
                retorno = [{
						"id": m.id,
                        "orign_id": m.origin_id,
						"name": m.name,
						"id_parent": m.id_parent,
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

    @ns_cat.response(HTTPStatus.OK.value,"Cria uma nova categoria de produto no sistema")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova categoria de produto!")
    @ns_cat.doc(body=cat_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            cat = CmmCategories()
            cat.name = req["name"]
            cat.id_parent = int(req["id_parent"]) if req["id_parent"] is not None else None
            db.session.add(cat)
            db.session.commit()
            return cat.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_cat.route("/<int:id>")
class CategoryApi(Resource):
    @ns_cat.response(HTTPStatus.OK.value,"Obtem um registro de uma categoria",cat_model)
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmCategories.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_cat.response(HTTPStatus.OK.value,"Atualiza os dados de uma categoria")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            cat = CmmCategories.query.get(id)
            cat.name      = cat.name if request.form.get("name") is None else request.form.get("name")
            cat.id_parent = cat.id_parent if request.form.get("id_parent") is None else int(request.form.get("id_parent"))
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_cat.response(HTTPStatus.OK.value,"Exclui os dados de uma categoria")
    @ns_cat.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            cat = CmmCategories.query.get(id)
            cat.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }