from http import HTTPStatus
from flask_restx import Resource, fields, Namespace
from flask import request
from models import _get_params,CrmFunnel, CrmFunnelStage, db
# from models import _show_query
from sqlalchemy import Update, desc, exc, and_, asc, Select
from auth import auth
from os import environ

ns_funil = Namespace("funnels",description="Operações para manipular funis de clientes")

fun_pag_model = ns_funil.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

fun_stg_model = ns_funil.model(
    "FunnelStage",{
        "id": fields.Integer,
        "name": fields.String,
        "icon": fields.String,
        "order": fields.Integer,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

fun_model = ns_funil.model(
    "Funnel",{
        "id": fields.Integer,
        "name": fields.String,
        "stages": fields.List(fields.Nested(fun_stg_model)),
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

fun_return = ns_funil.model(
    "FunnelReturn",{
        "pagination": fields.Nested(fun_pag_model),
        "data": fields.List(fields.Nested(fun_model))
    }
)


@ns_funil.route("/")
class FunnelList(Resource):
    @ns_funil.response(HTTPStatus.OK.value,"Obtem a listagem de funis",fun_return)
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_funil.param("page","Número da página de registros","query",type=int,required=True)
    @ns_funil.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_funil.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query   = "" if request.args.get("query") is None else request.args.get("query")
    
        try:
            params = _get_params(query)
            trash     = False if hasattr(params,'trash')==False else True
            list_all  = False if hasattr(params,"list_all")==False else True
            order_by  = "id" if hasattr(params,"order_by")==False else params.order_by
            direction = desc if hasattr(params,"order_dir") == 'DESC' else asc
            search    = None if hasattr(params,"search")==False or params.search=='' else params.search

            filter_type    = None if hasattr(params,"type")==False else params.type
            filter_default = None if hasattr(params,"default")==False else True if params.default=="1" else False

            rquery = Select(CrmFunnel.id,
                            CrmFunnel.name,
                            CrmFunnel.is_default,
                            CrmFunnel.date_created,
                            CrmFunnel.date_updated,
                            CrmFunnel.type)\
                            .where(CrmFunnel.trash==trash)\
                            .order_by(direction(getattr(CrmFunnel,order_by)))

            if search is not None:
                rquery = rquery.where(CrmFunnel.name.like("%{}%".format(search)))

            if filter_type is not None:
                rquery = rquery.where(CrmFunnel.type==filter_type)

            if filter_default is not None:
                rquery = rquery.filter(CrmFunnel.is_default==filter_default)

            if list_all==False:
                pag    = db.paginate(rquery,page=pag_num,per_page=pag_size)
                rquery = rquery.limit(pag_size).offset((pag_num - 1) * pag_size)
                return {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next
                    },
                    "data":[{
                        "id": m.id,
                        "name": m.name,
                        "is_default": m.is_default,
                        "type":m.type,
                        "stages": self.get_stages(m.id),
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                return [{
                        "id": m.id,
                        "name": m.name,
                        "is_default": m.is_default,
                        "type":m.type,
                        "stages": self.get_stages(m.id),
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    def get_stages(self,id:int):
        rquery = CrmFunnelStage.query.filter(and_(CrmFunnelStage.id_funnel==id,CrmFunnelStage.trash.is_(False))).order_by(asc(CrmFunnelStage.order))
        return [{
            "id": m.id,
            "name": m.name,
            "icon": m.icon,
            "icon_color": m.icon_color,
            "color": m.color,
            "order": m.order,
            "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
            "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
        } for m in rquery]

    @ns_funil.response(HTTPStatus.OK.value,"cria um novo funil")
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo funil!")
    @ns_funil.doc(body=fun_model)
    @auth.login_required
    def post(self)->int|dict:
        try:
            req = request.get_json()

            #so pode haver um default
            if req["is_default"]==1 or req["is_default"]=="true":
                db.session.execute(Update(CrmFunnel).values(is_default=0))
                db.session.commit()

            fun:CrmFunnel  = CrmFunnel()
            fun.name       = req["name"]
            fun.is_default = False if req["is_default"]=='false' or req["is_default"]==0 else True
            fun.type       = req["type"]
            db.session.add(fun)
            db.session.commit()

            if "stages" in req:
                for stg in req["stages"]:
                    stage = CrmFunnelStage()
                    stage.name = stg["name"]
                    stage.id_funnel = fun.id
                    stage.order = stg["order"]
                    db.session.add(stage)
                    db.session.commit()
            return fun.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_funil.response(HTTPStatus.OK.value,"Exclui os dados de um funil")
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def delete(self)->bool:
        try:
            req = request.get_json()
            for id in req["ids"]:
                fun = CrmFunnel.query.get(id)
                fun.trash = req["toTrash"]
                db.session.commit()
            return True
        except Exception:
            return False

@ns_funil.route("/<int:id>")
@ns_funil.param("id","Id do registro")
class FunnelApi(Resource):
    @ns_funil.response(HTTPStatus.OK.value,"Obtem um registro de um funil",fun_model)
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def get(self,id:int):
        try:
            rquery = CrmFunnel.query.get(id)
            squery = Select(CrmFunnelStage.id,
                            CrmFunnelStage.name,
                            CrmFunnelStage.order,
                            CrmFunnelStage.date_created,
                            CrmFunnelStage.date_updated)\
                            .where(CrmFunnelStage.id_funnel==id)
            return {
                "id": rquery.id,
                "name": rquery.name,
                "type": rquery.type,
                "is_default": rquery.is_default,
                "date_created": rquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": None if rquery.date_updated is None else rquery.date_updated.strftime("%Y-%m-%d %H:%M:%S"),
                "stages": [{
                    "id": m.id,
                    "name": m.name,
                    "order": m.order,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": None if m.date_updated is None else m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
                }for m in db.session.execute(squery)]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_funil.response(HTTPStatus.OK.value,"Atualiza dados de um funil")
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_funil.param("name","Nome do funil",required=True)
    @auth.login_required
    def post(self,id:int)->bool|dict:
        try:
            req = request.get_json()

            #so pode haver um default
            if req["is_default"]==1 or req["is_default"]=="true":
                db.session.execute(Update(CrmFunnel).values(is_default=0))
                db.session.commit()
            
            fun:CrmFunnel  = CrmFunnel.query.get(id)
            fun.name       = req["name"]
            fun.is_default = 1 if req["is_default"]==1 or req["is_default"]=="true" else 0
            fun.type       = req["type"]
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }