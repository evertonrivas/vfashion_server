from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmProductsTypes,db
from sqlalchemy import and_,exc,asc,desc
from auth import auth

ns_type = Namespace("products-type",description="Operações para manipular dados de tipos de produtos")

type_pag_model = ns_type.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

type_model = ns_type.model(
    "ProductType",{
        "id": fields.Integer,
        "name": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

type_return = ns_type.model(
    "ProductTypeReturn",{
        "pagination": fields.Nested(type_pag_model),
        "data": fields.List(fields.Nested(type_model))
    }
)

@ns_type.route("/")
class CategoryList(Resource):
    @ns_type.response(HTTPStatus.OK.value,"Obtem a listagem de categorias de tipos de produto",type_return)
    @ns_type.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_type.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_type.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_type.param("query","Texto para busca","query")
    @ns_type.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_type.param("order_by","Campo de ordenacao","query")
    @ns_type.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num    =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size   = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search     = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        list_all   = False if request.args.get("list_all") is None else True
        order_by   = "id" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc
        try:
            if search=="":
                rquery = CmmProductsTypes\
                    .query\
                    .filter(CmmProductsTypes.trash==False)\
                    .order_by(direction(getattr(CmmProductsTypes, order_by)))
            else:
                rquery = CmmProductsTypes\
                    .query\
                    .filter(and_(CmmProductsTypes.trash==False,CmmProductsTypes.name.like(search)))\
                    .order_by(direction(getattr(CmmProductsTypes, order_by)))

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

    @ns_type.response(HTTPStatus.OK.value,"Cria um novo tipo de produto no sistema")
    @ns_type.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo tipo de produto!")
    @ns_type.doc(body=type_model)
    @auth.login_required
    def post(self):
        try:
            type = CmmProductsTypes()
            type.name = request.form.get("name")
            db.session.add(type)
            db.session.commit()
            return type.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_type.route("/<int:id>")
class CategoryApi(Resource):
    @ns_type.response(HTTPStatus.OK.value,"Obtem um registro de um tipo de produto",type_model)
    @ns_type.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmProductsTypes.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_type.response(HTTPStatus.OK.value,"Atualiza os dados de um tipo de produto")
    @ns_type.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            cat = CmmProductsTypes.query.get(id)
            cat.name = cat.name if request.form.get("name") is None else request.form.get("name")
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_type.response(HTTPStatus.OK.value,"Exclui os dados de um tipo de produto")
    @ns_type.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            cat = CmmProductsTypes.query.get(id)
            cat.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }