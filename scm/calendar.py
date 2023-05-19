from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import db,ScmCalendar,ScmEvent,ScmEventType
from sqlalchemy import exc, asc,between,Select,and_,desc
from auth import auth
from datetime import datetime

ns_calendar = Namespace("calendar",description="Operações para manipular dados de cidades")

evt_model = ns_calendar.model(
    "Event",{
        "name": fields.String,
        "start": fields.Date,
        "end": fields.Date,
        "type": fields.String
    }
)


@ns_calendar.route("/")
class CalendarList(Resource):
    @ns_calendar.response(HTTPStatus.OK.value,"Obtem a listagem de cidades")
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_calendar.param("query","Texto para busca de intervalos de datas e eventos","query")
    #@auth.login_required
    def get(self):
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
            dates = search.split(",")
            if dates[0].replace("is:start ","")=="":
                dt_start = datetime.now().strftime("%Y-01-01")
                dt_end   = datetime.now().strftime("%Y-12-31")
            else:
                dt_start = dates[0].replace("is:start ","")
                dt_end   = dates[1].replace("is:end ","")

            yquery = Select(ScmCalendar.year).distinct()\
                .where(between(ScmCalendar.calendar_date,dt_start,dt_end))\
                .where(ScmCalendar.day_of_week==7)\
                .order_by(asc(ScmCalendar.time_id))

            retorno = [{
                    "year": y.year,
                    "months": [{
                        "position": m.month,
                        "weeks": self.__get_weeks(dt_start,dt_end,y.year,m.month)
                    }for m in self.__get_months(dt_start,dt_end,y.year)],
                } for y in db.session.execute(yquery).all()]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    def __get_months(self,dt_start,dt_end,_current_year):
        return db.session.execute(Select(ScmCalendar.month).distinct()\
            .where(between(ScmCalendar.calendar_date,dt_start,dt_end))\
            .where(ScmCalendar.year==_current_year)\
            .where(ScmCalendar.day_of_week==7)\
            .order_by(asc(ScmCalendar.time_id))
        ).all()
    
    def __get_weeks(self,dt_start,dt_end,_current_year,_current_month):
        weeks = []
        for w in db.session.execute(Select(ScmCalendar.week).distinct()\
            .where(between(ScmCalendar.calendar_date,dt_start,dt_end))\
            .where(and_(ScmCalendar.year==_current_year,ScmCalendar.month==_current_month))\
            .where(ScmCalendar.day_of_week==7)\
            .order_by(asc(ScmCalendar.time_id))
        ).all():
            weeks.append(w.week)
        return weeks

    @ns_calendar.response(HTTPStatus.OK.value,"Salva um evento no calendário",evt_model)
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Falha salvar registro!")
    def post(self):
        try:
            req = request.get_json()
            date_start = datetime.strptime(req["date_start"],"%Y-%m-%d")
            date_end   = datetime.strptime(req["date_end"],"%Y-%m-%d")

            ord = db.session.execute(Select(ScmEvent.order).limit(1).order_by(desc(ScmEvent.order))).one()
            print(ord)

            reg = ScmEvent()
            reg.name          = req["name"]
            reg.year          = date_start.year
            reg.start_week    = date_start.isocalendar().week
            reg.end_week      = date_end.isocalendar().week
            reg.id_event_type = req["id_event_type"]
            reg.id_collection = None if req["id_collection"] is None or req["id_collection"]=="" else req["id_collection"]
            reg.budget_value  = None if req["budget_value"] is None or req["budget_value"]=="" else reg["budget_value"]
            reg.order = ord.order+1
            
            db.session.add(reg)
            db.session.commit()

            return reg.id
            
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_calendar.response(HTTPStatus.OK.value,"Exclui os dados de varios eventos")
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for r in req:
                it = ScmEvent.query.get(r)
                db.session.delete(it)
                db.session.commit()
            
            return True
        except exc.SQLAlchemyError as e:
            pass

@ns_calendar.route("/<int:id>")
@ns_calendar.param("id","Id do registro")
class CalendarEventApi(Resource):
    @ns_calendar.response(HTTPStatus.OK.value,"Retorna os dados de um evento")
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            qry = ScmEvent.query.get(id)

            return {
                "id": qry.id,
                "name": qry.name,
                "year": qry.year,
                "start_week": qry.start_week,
                "end_week": qry.end_week,
                "id_event_type": qry.id_event_type,
                "id_collection": qry.id_collection,
                "budget_value": qry.budget_value,
                "date_created": qry.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": qry.date_updated.strftime("%Y-%m-%d %H:%M:%S") if qry.date_updated!=None else None
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_calendar.response(HTTPStatus.OK.value,"Atualiza os dados de um evento")
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_calendar.doc(body=evt_model)
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            date_start = datetime.strptime(req["date_start"],"%Y-%m-%d")
            date_end   = datetime.strptime(req["date_end"],"%Y-%m-%d")

            reg = ScmEvent.query.get(id)
            reg.name          = req["name"]
            reg.year          = date_start.year
            reg.start_week    = date_start.isocalendar().week
            reg.end_week      = date_end.isocalendar().week
            reg.id_event_type = req["id_event_type"]
            reg.id_collection = None if req["id_collection"] is None else req["id_collection"]
            reg.budget_value  = None if req["budget_value"] is None else reg["budget_value"]
            db.session.commit()

            return True
            
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_calendar.response(HTTPStatus.OK.value,"Exclui os dados de um tipo de evento")
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        pass

class CalendarEventList(Resource):
    @ns_calendar.response(HTTPStatus.OK.value,"Obtem a listagem de cidades")
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_calendar.param("query","Texto para busca de intervalos de datas e eventos","query")
    def get(self):
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
            dates = search.split(",")
            if dates[0].replace("is:start ","")=="":
                dt_start = datetime.now().strftime("%Y-01-01")
                dt_end   = datetime.now().strftime("%Y-12-31")
            else:
                dt_start = dates[0].replace("is:start ","")
                dt_end   = dates[1].replace("is:end ","")

            yquery = Select(ScmEvent.id,
                            ScmEvent.name,
                            ScmEvent.year,
                            ScmEvent.start_week,
                            ScmEvent.end_week,
                            ScmEvent.budget_value,
                            ScmEventType.id.label("id_event_type"),
                            ScmEventType.name.label("event_type_name"),
                            ScmEventType.hex_color,
                            ScmEventType.has_budget).distinct()\
                .join(ScmEventType,ScmEventType.id==ScmEvent.id_event_type)\
                .join(ScmCalendar,and_(ScmEvent.year==ScmCalendar.year,ScmEvent.start_week==ScmCalendar.week))\
                .where(between(ScmCalendar.calendar_date,dt_start,dt_end))\
                .order_by(asc(ScmEvent.order))

            retorno = [{
                    "name": e.name,
                    "start_week":e.start_week,
                    "end_week":e.end_week,
                    "year":e.year,
                    "type": {
                        "id": e.id_event_type,
                        "name": e.event_type_name,
                        "hex_color": e.hex_color,
                        "has_budget": e.has_budget
                    }
                } for e in db.session.execute(yquery).all()]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


ns_calendar.add_resource(CalendarEventList,"/events")