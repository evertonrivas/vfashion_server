from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmTranslateSizes,db
from sqlalchemy import exc, and_,desc,asc
from auth import auth

ns_size = Namespace("translate-sizes",description="Operações para manipular dados de tamanhos")

color_pag_model = ns_size.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

color_model = ns_size.model(
    "TranslateSize",{
        "id": fields.Integer,
        "hexcode": fields.String,
        "color": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

model_return = ns_size.model(
    "TranslateSizeReturn",{
        "pagination": fields.Nested(color_pag_model),
        "data": fields.List(fields.Nested(color_model))
    }
)

@ns_size.route("/")
class CategoryList(Resource):
    @ns_size.response(HTTPStatus.OK.value,"Obtem a listagem de traduções de tamanhos",model_return)
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
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        list_all = False if request.args.get("list_all") is None else True
        order_by   = "id" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc
        try:
            if search=="":
                rquery = CmmTranslateSizes\
                    .query\
                    .filter(CmmTranslateSizes.trash==False)\
                    .order_by(direction(getattr(CmmTranslateSizes, order_by)))
            else:
                rquery = CmmTranslateSizes\
                    .query\
                    .filter(and_(CmmTranslateSizes.trash==False,CmmTranslateSizes.color.like(search)))\
                    .order_by(direction(getattr(CmmTranslateSizes, order_by)))

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
                        "size_name": m.size_name,
                        "size": m.size,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in rquery.items]
                }
            else:
                retorno = [{
                        "id": m.id,
                        "size_name": m.size_name,
                        "size": m.size,
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

    @ns_size.response(HTTPStatus.OK.value,"Cria uma nova tradução de tamanho")
    @ns_size.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo modelo de produto!")
    @ns_size.doc(body=color_model)
    @auth.login_required
    def post(self):
        try:
            cor = CmmTranslateSizes()
            cor.size_name = request.form.get("size_name")
            cor.size      = request.form.get("size")
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
    @ns_size.response(HTTPStatus.OK.value,"Obtem um registro de uma nova tradução de tamanho",color_model)
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
            cor.size_name = cor.hexcode if request.form.get("size_name") is None else request.form.get("size_name")
            cor.size      = cor.color if request.form.get("size") is None else request.form.get("size")
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