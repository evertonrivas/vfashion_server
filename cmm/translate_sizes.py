from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmTranslateSizes, _get_params,db
from sqlalchemy import Select, exc, and_,desc,asc
from auth import auth
from config import Config

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
    @ns_size.response(HTTPStatus.OK.value,"Obtem a listagem de traduções de tamanhos",size_return)
    @ns_size.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_size.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_size.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_size.param("query","Texto para busca","query")
    @ns_size.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_size.param("order_by","Campo de ordenacao","query")
    @ns_size.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        try:
            params = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            trash     = False if hasattr(params,'active')==False else True
            list_all  = False if hasattr(params,'list_all')==False else True

            rquery = Select(CmmTranslateSizes.id,
                            CmmTranslateSizes.new_size,
                            CmmTranslateSizes.size,
                            CmmTranslateSizes.date_created,
                            CmmTranslateSizes.date_updated)\
                            .where(CmmTranslateSizes.trash==trash)\
                            .order_by(direction(getattr(CmmTranslateSizes,order_by)))

            if search is not None:
                rquery = rquery.where(CmmTranslateSizes.new_size.like("%{}%".format(search)))

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
                        "new_size": m.new_size,
                        "size": m.size,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id": m.id,
                        "new_size": m.new_size,
                        "size": m.size,
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

    @ns_size.response(HTTPStatus.OK.value,"Cria uma nova tradução de tamanho")
    @ns_size.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo modelo de produto!")
    @ns_size.doc(body=size_model)
    @auth.login_required
    def post(self):
        try:
            cor = CmmTranslateSizes()
            cor.new_size = request.form.get("size_name")
            cor.size     = request.form.get("size")
            db.session.add(type)
            db.session.commit()
            return type.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_size.route("/<int:id>")
class CategoryApi(Resource):
    @ns_size.response(HTTPStatus.OK.value,"Obtem um registro de uma nova tradução de tamanho",size_model)
    @ns_size.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmTranslateSizes.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_size.response(HTTPStatus.OK.value,"Atualiza os dados de uma nova tradução de tamanho")
    @ns_size.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            cor = CmmTranslateSizes.query.get(id)
            cor.new_size = cor.hexcode if request.form.get("size_name") is None else request.form.get("size_name")
            cor.size     = cor.color if request.form.get("size") is None else request.form.get("size")
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_size.response(HTTPStatus.OK.value,"Exclui os dados de uma nova tradução de tamanho")
    @ns_size.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            cor = CmmTranslateSizes.query.get(id)
            cor.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }