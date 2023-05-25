from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bBrand, B2bCollection, db,ScmCalendar,ScmEvent,ScmEventType
from sqlalchemy import exc, asc,between,Select,and_
from auth import auth
from datetime import datetime,date

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

            reg = ScmEvent()
            reg.name          = req["name"]
            reg.year          = date_start.year
            reg.start_date    = date_start
            reg.end_date      = date_end
            reg.id_event_type = req["id_event_type"]
            reg.id_collection = None if req["id_collection"] is None or req["id_collection"]=="" else req["id_collection"]
            reg.budget_value  = None if req["budget_value"] is None or req["budget_value"]=="" else reg["budget_value"]
            
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
                "start_week": date(qry.start_date.year,qry.end_date.month,qry.end_date.day).isocalendar().week,
                "end_week": date(qry.end_date.year,qry.end_date.month,qry.end_date.day).isocalendar().week,
                "start_date": qry.start_date,
                "end_date": qry.end_date,
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
            reg.start_date    = date_start
            reg.end_date      = date_end
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
    @ns_calendar.param("milestone","Se é marco do calendário ou não","query",type=bool)
    def get(self):
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        milestone = False if request.args.get("milestone") is None else False if request.args.get("milestone")=="false" else True

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
                            ScmEvent.start_date,
                            ScmEvent.end_date,
                            ScmEvent.budget_value,
                            ScmEventType.id.label("id_event_type"),
                            ScmEventType.name.label("event_type_name"),
                            ScmEventType.hex_color,
                            ScmEventType.has_budget,
                            ScmEventType.is_milestone,
                            B2bCollection.id.label("id_collection"),
                            B2bCollection.name.label("collection_name"),
                            B2bBrand.id.label("id_brand"),
                            B2bBrand.name.label("brand_name")).distinct()\
                .join(ScmEventType,ScmEventType.id==ScmEvent.id_event_type)\
                .join(ScmCalendar,and_(ScmEvent.year==ScmCalendar.year,ScmEvent.start_date==ScmCalendar.calendar_date))\
                .outerjoin(B2bCollection,ScmEvent.id_collection==B2bCollection.id)\
                .outerjoin(B2bBrand,B2bCollection.id_brand==B2bBrand.id)\
                .where(between(ScmCalendar.calendar_date,dt_start,dt_end))\
                .where(and_(ScmEventType.is_milestone==milestone,ScmEventType.id_parent.is_(None)))\
                .order_by(asc(ScmEvent.start_date))

            retorno = [{
                    "id": e.id,
                    "name": e.name,
                    "start_week": date(e.start_date.year,e.start_date.month,e.start_date.day).isocalendar().week,
                    "end_week": date(e.end_date.year,e.end_date.month,e.end_date.day).isocalendar().week,
                    "start_date": e.start_date.strftime("%x"),
                    "end_date": e.end_date.strftime("%x"),
                    "year":e.year,
                    "type": {
                        "id": e.id_event_type,
                        "name": e.event_type_name,
                        "hex_color": e.hex_color,
                        "has_budget": e.has_budget
                    },
                    "collection":{
                        "id":e.id_collection,
                        "name": e.collection_name,
                        "brand":{
                            "id": e.id_brand,
                            "name": e.brand_name
                        }
                    },
                    "children":self.__get_children(dt_start,dt_end,milestone,e.id)
                } for e in db.session.execute(yquery).all()]

            if milestone==True:
                retorno.append({
                    "id": 0,
                    "name": "Hoje",
                    "start_week": datetime.now().isocalendar().week,
                    "end_week": datetime.now().isocalendar().week,
                    "start_date": datetime.now().strftime("%x"),
                    "end_date": datetime.now().strftime("%x"),
                    "year": datetime.now().year,
                    "type":{
                        "id":0,
                        "name": "hoje",
                        "hex_color": '#20c997',
                        "has_budget": False
                    },
                    "collection":{
                        "id": 0,
                        "name":None,
                        "brand":{
                            "id":0,
                            "name": None
                        }
                    }
                })
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    def __get_children(self,p_dt_start:str,p_dt_end:str,p_milestone:bool,p_id_parent:int):
        yquery = Select(ScmEvent.id,
                            ScmEvent.name,
                            ScmEvent.year,
                            ScmEvent.start_date,
                            ScmEvent.end_date,
                            ScmEvent.budget_value,
                            ScmEventType.id.label("id_event_type"),
                            ScmEventType.name.label("event_type_name"),
                            ScmEventType.hex_color,
                            ScmEventType.has_budget,
                            ScmEventType.is_milestone,
                            B2bCollection.id.label("id_collection"),
                            B2bCollection.name.label("collection_name"),
                            B2bBrand.id.label("id_brand"),
                            B2bBrand.name.label("brand_name")).distinct()\
                .join(ScmEventType,ScmEventType.id==ScmEvent.id_event_type)\
                .join(ScmCalendar,and_(ScmEvent.year==ScmCalendar.year,ScmEvent.start_date==ScmCalendar.calendar_date))\
                .outerjoin(B2bCollection,ScmEvent.id_collection==B2bCollection.id)\
                .outerjoin(B2bBrand,B2bCollection.id_brand==B2bBrand.id)\
                .where(between(ScmCalendar.calendar_date,p_dt_start,p_dt_end))\
                .where(and_(ScmEventType.is_milestone==p_milestone,ScmEventType.id_parent==p_id_parent))\
                .order_by(asc(ScmEvent.start_date))
        
        return [{
            "id": e.id,
            "name": e.name,
            "start_week": date(e.start_date.year,e.start_date.month,e.start_date.day).isocalendar().week,
            "end_week": date(e.end_date.year,e.end_date.month,e.end_date.day).isocalendar().week,
            "start_date": e.start_date.strftime("%x"),
            "end_date": e.end_date.strftime("%x"),
            "year":e.year,
            "type": {
                "id": e.id_event_type,
                "name": e.event_type_name,
                "hex_color": e.hex_color,
                "has_budget": e.has_budget
            },
            "collection":{
                "id":e.id_collection,
                "name": e.collection_name,
                "brand":{
                    "id": e.id_brand,
                    "name": e.brand_name
                }
            }
        } for e in db.session.execute(yquery).all()]

ns_calendar.add_resource(CalendarEventList,"/events")