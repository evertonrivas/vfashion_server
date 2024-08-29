from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bProductStock, CmmTranslateColors, _get_params,db
from sqlalchemy import Select, exc, desc, asc
from auth import auth
from os import environ

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
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else request.args.get("query")
        try:
            params = _get_params(query)

            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            trash     = False if hasattr(params,'trash')==False else True
            list_all  = False if hasattr(params,'list_all')==False else True

            filter_b2b = False if hasattr(params,"b2b")==False else True

            rquery = Select(CmmTranslateColors.id,
                            CmmTranslateColors.hexcode,
                            CmmTranslateColors.name,
                            CmmTranslateColors.color,
                            CmmTranslateColors.date_created,
                            CmmTranslateColors.date_updated)\
                            .where(CmmTranslateColors.trash==trash)\
                            .order_by(direction(getattr(CmmTranslateColors,order_by)))
            
            if filter_b2b is True:
                rquery = rquery.where(
                    CmmTranslateColors.id.in_(
                        Select(B2bProductStock.id_color).distinct()
                    )
                )
            
            if search is not None:
                rquery = rquery.where(CmmTranslateColors.name.like("%{}%".format(search)))

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
                        "hexcode": m.hexcode,
                        "name": m.name,
                        "color": m.color,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id": m.id,
                        "hexcode": m.hexcode,
                        "name": m.name,
                        "color": m.color,
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

    @ns_color.response(HTTPStatus.OK.value,"Cria uma nova tradução de cor")
    @ns_color.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo modelo de produto!")
    @ns_color.doc(body=color_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            cor = CmmTranslateColors()
            cor.hexcode = req["hexcode"]
            cor.name    = req["name"]
            cor.color   = req["color"]
            db.session.add(cor)
            db.session.commit()
            return cor.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_color.response(HTTPStatus.OK.value,"Exclui os dados de uma nova tradução de tamanho")
    @ns_color.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self)->bool:
        try:
            req = request.get_json()
            for id in req["ids"]:
                cor = CmmTranslateColors.query.get(id)
                cor.trash = req["toTrash"]
                db.session.commit()
            return True
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