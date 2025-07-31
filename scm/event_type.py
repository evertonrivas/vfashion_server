from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from datetime import datetime
from models.helpers import db
from models.helpers import _get_params
from models.tenant import ScmEventType
from sqlalchemy import Select, exc, asc, desc
from flask_restx import Resource, Namespace, fields

ns_event = Namespace("event-type",description="Operações para manipular dados de tipos de eventos")

event_pag_model = ns_event.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

event_model = ns_event.model(
    "EventType",{
        "id": fields.Integer,
        "name": fields.String,
        "hex_color": fields.String,
        "has_budget": fields.Boolean,
        "use_collection": fields.Boolean
    }
)

event_return = ns_event.model(
    "BrandReturn",{
        "pagination": fields.Nested(event_pag_model),
        "data": fields.List(fields.Nested(event_model))
    }
)

@ns_event.route("/")
class CollectionList(Resource):
    @ns_event.response(HTTPStatus.OK,"Obtem registros de tipos de eventos",event_return)
    @ns_event.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @ns_event.param("page","Número da página de registros","query",type=int,required=True)
    @ns_event.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_event.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query    = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
            params    = _get_params(query)
            direction = asc if not hasattr(params,'order') else asc if params is not None and params.order=='ASC' else desc
            order_by  = 'id' if not hasattr(params,'order_by') else params.order_by if params is not None else 'id'
            trash     = False if not hasattr(params,'trash') else True
            list_all  = False if not hasattr(params,'list_all') else True
            
            filter_search       = None if not hasattr(params,"search") else params.search if params is not None else None
            filter_just_parent  = False if not hasattr(params,"just_parent") else True
            filter_no_milestone = False if not hasattr(params,"no_milestone") else True


            rquery = Select(ScmEventType.id,
                            ScmEventType.id_parent,
                            ScmEventType.name,
                            ScmEventType.hex_color,
                            ScmEventType.has_budget,
                            ScmEventType.use_collection,
                            ScmEventType.is_milestone,
                            ScmEventType.create_funnel,
                            ScmEventType.date_created,
                            ScmEventType.date_updated)\
                            .where(ScmEventType.trash==trash)\
                            .order_by(direction(getattr(ScmEventType,order_by)))
            
            squery = ScmEventType.query
            
            if filter_search is not None:
                rquery = rquery.where(ScmEventType.name.like("%{}%".format(filter_search)))

            if filter_just_parent:
                rquery = rquery.where(ScmEventType.id_parent.is_(None))

            if filter_no_milestone:
                rquery = rquery.where(ScmEventType.is_milestone.is_(False))

            if not list_all:
                pag    = db.paginate(rquery,page=pag_num,per_page=pag_size)
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
                        "name": m.name,
                        "hex_color": m.hex_color,
                        "has_budget": m.has_budget,
                        "use_collection": m.use_collection,
                        "is_milestone": m.is_milestone,
                        "create_funnel": m.create_funnel,
                        "children": [{
                            "id": c.id,
                            "name": c.name,
                            "hex_color": c.hex_color,
                            "has_budget": c.has_budget,
                            "is_milestone": c.is_milestone,
                            "use_collection": c.use_collection,
                            "create_funnel": c.create_funnel,
                            "date_created": c.date_created.strftime("%Y-%m-%d"),
                            "date_updated": c.date_updated.strftime("%Y-%m-%d %H:%M:%S") if c.date_updated is not None else None
                        }for c in squery.filter(ScmEventType.id_parent==m.id).all()],
                        "parent": self.__get_parent(m.id_parent),
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id":m.id,
                        "name":m.name,
                        "hex_color": m.hex_color,
                        "has_budget": m.has_budget,
                        "use_collection": m.use_collection,
                        "is_milestone": m.is_milestone,
                        "create_funnel": m.create_funnel,
                        "children": [{
                            "id": c.id,
                            "name": c.name,
                            "hex_color": c.hex_color,
                            "has_budget": c.has_budget,
                            "is_milestone": c.is_milestone,
                            "use_collection": c.use_collection,
                            "create_funnel": c.create_funnel,
                            "date_created": c.date_created.strftime("%Y-%m-%d"),
                            "date_updated": c.date_updated.strftime("%Y-%m-%d %H:%M:%S") if c.date_updated is not None else None
                        }for c in squery.filter(ScmEventType.id_parent==m.id).all()],
                        "parent": self.__get_parent(m.id_parent),
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
    
    def __get_parent(self,id_parent:int):
        reg = db.session.execute(Select(ScmEventType.id,
                      ScmEventType.name,
                      ScmEventType.hex_color,
                      ScmEventType.has_budget,
                      ScmEventType.use_collection,
                      ScmEventType.is_milestone,
                      ScmEventType.create_funnel,
                      ScmEventType.date_created,
                      ScmEventType.date_updated).where(ScmEventType.id==id_parent)).first()
        if reg is not None:
            return {
                "id": reg.id,
                "name": reg.name,
                "hex_color": reg.hex_color,
                "has_budget": reg.has_budget,
                "use_collection": reg.use_collection,
                "is_milestone": reg.is_milestone,
                "create_funnel": reg.create_funnel,
                "date_created": reg.date_created.strftime("%Y-%m-%d"),
                "date_updated": reg.date_updated.strftime("%Y-%m-%d %H:%M:%S") if reg.date_updated is not None else None
            }
        else:
            return {}

    @ns_event.response(HTTPStatus.OK,"Cria um novo tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST,"Falha ao criar registro!")
    @ns_event.doc(body=event_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            reg = ScmEventType()
            reg.name           = req["name"]
            reg.hex_color      = req["hex_color"]
            setattr(reg,"has_budget",(False if req["has_budget"]=='false' else True))
            setattr(reg,"use_collection",(False if req["use_collection"]=='false' else True))
            setattr(reg,"is_milestone",(False if req["is_milestone"]=='false' else True))
            setattr(reg,"create_funnel",(False if req["create_funnel"]=='false' else True))
            if reg.create_funnel is True:
                setattr(reg,"use_collection",True) # forca o uso de colecao quando houver criacao de Funil
            setattr(reg,"date_created", datetime.now())
            db.session.add(reg)
            db.session.commit()

            return reg.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_event.response(HTTPStatus.OK,"Exclui os dados de um tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self)->bool|dict:
        try:
            req = request.get_json()
            for id in req["ids"]:
                reg:ScmEventType|None = ScmEventType.query.get(id)
                setattr(reg,"trash",req["toTrash"])
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_event.route("/<int:id>")
@ns_event.param("id","Id do registro")
class CollectionApi(Resource):
    @ns_event.response(HTTPStatus.OK,"Retorna os dados de um tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            qry = ScmEventType.query.get(id)
            if qry is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST

            return {
                "id": qry.id,
                "name": qry.name,
                "hex_color": qry.hex_color,
                "has_budget": qry.has_budget,
                "is_milestone": qry.is_milestone,
                "use_collection": qry.use_collection,
                "create_funnel": qry.create_funnel,
                "date_created": qry.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": qry.date_updated.strftime("%Y-%m-%d %H:%M:%S") if qry.date_updated is not None else None
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_event.response(HTTPStatus.OK,"Atualiza os dados de um tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @ns_event.doc(body=event_model)
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            reg:ScmEventType|None = ScmEventType.query.get(id)
            if reg is None:
                return {"error":"Registro não encontrado!"}, HTTPStatus.BAD_REQUEST
            reg.name           = req["name"]
            reg.hex_color      = req["hex_color"]
            setattr(reg,"has_budget",(False if req["has_budget"]=='false' else True))
            setattr(reg,"use_collection",(False if req["use_collection"]=='false' else True))
            setattr(reg,"is_milestone",(False if req["is_milestone"]=='false' else True))
            setattr(reg,"create_funnel",(False if req["create_funnel"]=='false' else True))
            if reg.create_funnel is True:
                setattr(reg,"use_collection",True) # forca o uso de colecao quando houver criacao de Funil
            setattr(reg,"date_updated",datetime.now())
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }