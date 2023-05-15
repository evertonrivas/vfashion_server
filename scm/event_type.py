from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import db,ScmEventType
import json
from sqlalchemy import exc,and_,asc,desc
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
        "hex_color": fields.String
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
    @ns_event.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_event.param("order_by","Campo de ordenacao","query")
    @ns_event.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        list_all = False if request.args.get("list_all") is None else True
        order_by = "name" if request.args.get("order_by") is None else request.args.get("order_by")
        direction = asc if request.args.get("order_dir") == 'ASC' else desc

        try:
            if search=="":
                rquery = ScmEventType\
                    .query\
                    .filter(ScmEventType.trash == False)\
                    .order_by(direction(getattr(ScmEventType,order_by)))
                
            else:
                rquery = ScmEventType\
                    .query\
                    .filter(and_(ScmEventType.trash == False,ScmEventType.name.like(search)))\
                    .order_by(direction(getattr(ScmEventType,order_by)))

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
                        "hex_color": m.hex_color,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in rquery.items]
                }
            else:
                retorno = [{
                        "id":m.id,
                        "name":m.name,
                        "hex_color": m.hex_color,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in rquery.all()]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_event.response(HTTPStatus.OK.value,"Cria um novo tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_event.doc(body=event_model)
    @auth.login_required
    def post(self)->int:
        try:
            req = request.get_json()
            reg = ScmEventType()
            reg.name = req.name
            reg.hex_color = reg.hex_color
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
    @ns_event.response(HTTPStatus.OK.value,"Retorna os dados dados de um tipo de evento")
    @ns_event.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            qry = ns_event.query.get(id)

            return {
                "id": qry.id,
                "name": qry.name,
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
            req = json.dumps(request.get_json())
            reg = ScmEventType.query.get(id)
            reg.name      = reg.name if req.name is None else req.name
            reg.hex_color = reg.hex_color if req.hex_color is None else reg.hex_color
            reg.trash     = reg.trash if req.trash is None else req.trash
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
            reg = ScmEventType.query.get(id)
            reg.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }