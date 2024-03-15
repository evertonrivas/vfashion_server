from datetime import datetime
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import _get_params, _show_query, db,ScmEventType
import json
from sqlalchemy import Select, exc,and_,asc,desc
from auth import auth
from config import Config

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
    @ns_event.response(HTTPStatus.OK.value,"Obtem registros de tipos de eventos",event_return)
    @ns_event.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_event.param("page","Número da página de registros","query",type=int,required=True)
    @ns_event.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_event.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
            params    = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            trash     = False if hasattr(params,'active')==False else True
            list_all  = False if hasattr(params,'list_all')==False else True
            
            filter_search       = None if hasattr(params,"search")==False or str(params.search).strip()=="" else params.search
            filter_just_parent  = False if hasattr(params,"just_parent")==False else True
            filter_no_milestone = False if hasattr(params,"no_milestone")==False else True


            rquery = Select(ScmEventType.id,
                            ScmEventType.id_parent,
                            ScmEventType.name,
                            ScmEventType.hex_color,
                            ScmEventType.has_budget,
                            ScmEventType.use_collection,
                            ScmEventType.is_milestone,
                            ScmEventType.date_created,
                            ScmEventType.date_updated)\
                            .where(ScmEventType.trash==trash)\
                            .order_by(direction(getattr(ScmEventType,order_by)))
            
            squery = ScmEventType.query
            
            if filter_search is not None:
                rquery = rquery.where(ScmEventType.name.like("%{}%".format(filter_search)))

            if filter_just_parent==True:
                rquery = rquery.where(ScmEventType.id_parent.is_(None))

            if filter_no_milestone==True:
                rquery = rquery.where(ScmEventType.is_milestone==False)

            if list_all==False:
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
                        "children": [{
                            "id": c.id,
                            "name": c.name,
                            "hex_color": c.hex_color,
                            "has_budget": c.has_budget,
                            "use_collection": c.use_collection,
                            "is_milestone": c.is_milestone,
                            "date_created": c.date_created.strftime("%Y-%m-%d"),
                            "date_updated": c.date_updated.strftime("%Y-%m-%d %H:%M:%S") if c.date_updated!=None else None
                        }for c in squery.filter(ScmEventType.id_parent==m.id).all()],
                        "parent": self.__get_parent(m.id_parent),
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
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
                        "children": [{
                            "id": c.id,
                            "name": c.name,
                            "hex_color": c.hex_color,
                            "has_budget": c.has_budget,
                            "use_collection": c.use_collection,
                            "is_milestone": c.is_milestone,
                            "date_created": c.date_created.strftime("%Y-%m-%d"),
                            "date_updated": c.date_updated.strftime("%Y-%m-%d %H:%M:%S") if c.date_updated!=None else None
                        }for c in squery.filter(ScmEventType.id_parent==m.id).all()],
                        "parent": self.__get_parent(m.id_parent),
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
    
    def __get_parent(self,id_parent:int):
        reg = db.session.execute(Select(ScmEventType.id,
                      ScmEventType.name,
                      ScmEventType.hex_color,
                      ScmEventType.has_budget,
                      ScmEventType.use_collection,
                      ScmEventType.is_milestone,
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
                "date_created": reg.date_created.strftime("%Y-%m-%d"),
                "date_updated": reg.date_updated.strftime("%Y-%m-%d %H:%M:%S") if reg.date_updated!=None else None
            }
        else:
            return {}

    @ns_event.response(HTTPStatus.OK.value,"Cria um novo tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_event.doc(body=event_model)
    @auth.login_required
    def post(self)->int:
        try:
            req = request.get_json()
            reg = ScmEventType()
            reg.name           = req["name"]
            reg.hex_color      = req["hex_color"]
            reg.has_budget     = req["has_budget"]
            reg.use_collection = req["use_collection"]
            reg.is_milestone   = req["is_miliestone"]
            reg.id_parent      = req["id_parent"]
            reg.trash          = False
            reg.date_created   = datetime.now()
            db.session.add(reg)
            db.session.commit()

            return reg.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_event.route("/<int:id>")
@ns_event.param("id","Id do registro")
class CollectionApi(Resource):
    @ns_event.response(HTTPStatus.OK.value,"Retorna os dados de um tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            qry = ScmEventType.query.get(id)

            return {
                "id": qry.id,
                "name": qry.name,
                "hex_color": qry.hex_color,
                "has_budget": qry.has_budget,
                "use_collection": qry.use_collection,
                "date_created": qry.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": qry.date_updated.strftime("%Y-%m-%d %H:%M:%S") if qry.date_updated!=None else None
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_event.response(HTTPStatus.OK.value,"Atualiza os dados de um tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_event.doc(body=event_model)
    @auth.login_required
    def post(self,id:int)->bool:
        try:
            req = request.get_json()
            reg:ScmEventType = ScmEventType.query.get(id)
            reg.name           = req["name"]
            reg.hex_color      = req["hex_color"]
            reg.has_budget     = req["has_budget"]
            reg.use_collection = req["use_collection"]
            reg.is_milestone   = req["is_miliestone"]
            reg.id_parent      = req["id_parent"]
            reg.trash          = False
            reg.date_updated   = datetime.now()
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_event.response(HTTPStatus.OK.value,"Exclui os dados de um tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int)->bool:
        try:
            reg:ScmEventType = ScmEventType.query.get(id)
            reg.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }