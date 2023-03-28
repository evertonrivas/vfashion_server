from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmTranslateColors,db
from sqlalchemy import exc, and_,desc,asc
from auth import auth

ns_color = Namespace("translate-colors",description="Operações para manipular dados de cores")

color_pag_model = ns_color.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

color_model = ns_color.model(
    "ColorTranslate",{
        "id": fields.Integer,
        "hexcode": fields.String,
        "name": fields.String,
        "color": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

model_return = ns_color.model(
    "ColorTranslateReturn",{
        "pagination": fields.Nested(color_pag_model),
        "data": fields.List(fields.Nested(color_model))
    }
)

@ns_color.route("/")
class CategoryList(Resource):
    @ns_color.response(HTTPStatus.OK.value,"Obtem a listagem de traduções de cores",model_return)
    @ns_color.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_color.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_color.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_color.param("query","Texto para busca","query")
    @ns_color.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_color.param("order_by","Campo de ordenacao","query")
    @ns_color.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
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
                rquery = CmmTranslateColors\
                    .query\
                    .filter(CmmTranslateColors.trash==False)\
                    .order_by(direction(getattr(CmmTranslateColors, order_by)))
            else:
                rquery = CmmTranslateColors\
                    .query\
                    .filter(and_(CmmTranslateColors.trash==False,CmmTranslateColors.color.like(search)))\
                    .order_by(direction(getattr(CmmTranslateColors, order_by)))

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
                        "hexcode": m.hexcode,
                        "name": m.name,
                        "color": m.color,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in rquery.items]
                }
            else:
                retorno = [{
                        "id": m.id,
                        "hexcode": m.hexcode,
                        "name": m.name,
                        "color": m.color,
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

    @ns_color.response(HTTPStatus.OK.value,"Cria uma nova tradução de cor")
    @ns_color.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo modelo de produto!")
    @ns_color.doc(body=color_model)
    @auth.login_required
    def post(self):
        try:
            cor = CmmTranslateColors()
            cor.hexcode = request.form.get("hexcode")
            cor.name    = request.form.get("name")
            cor.color   = request.form.get("color")
            db.session.add(type)
            db.session.commit()
            return type.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_color.route("/<int:id>")
class CategoryApi(Resource):
    @ns_color.response(HTTPStatus.OK.value,"Obtem um registro de uma nova tradução de cor",color_model)
    @ns_color.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmTranslateColors.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_color.response(HTTPStatus.OK.value,"Atualiza os dados de uma nova tradução de cor")
    @ns_color.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            cor = CmmTranslateColors.query.get(id)
            cor.hexcode = cor.hexcode if request.form.get("hexcode") is None else request.form.get("hexcode")
            cor.name    = cor.name if request.form.get("name") is None else request.form.get("name")
            cor.color   = cor.color if request.form.get("color") is None else request.form.get("color")
            db.session.commit() 
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_color.response(HTTPStatus.OK.value,"Exclui os dados de uma nova tradução de tamanho")
    @ns_color.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            cor = CmmTranslateColors.query.get(id)
            cor.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }