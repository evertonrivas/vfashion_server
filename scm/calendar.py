from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import db,ScmCalendar
from sqlalchemy import desc, exc, asc,between,Date,Select
from auth import auth
from config import Config

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
class CategoryList(Resource):
    @ns_calendar.response(HTTPStatus.OK.value,"Obtem a listagem de cidades")
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_calendar.param("query","Texto para busca de intervalos de datas e eventos","query")
    #@auth.login_required
    def get(self):
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
            dates = search.split(",")
            dt_start = dates[0].replace("is:start ","")
            dt_end   = dates[1].replace("is:end ","")

            rquery = Select(ScmCalendar.year,ScmCalendar.month,ScmCalendar.week).distinct()\
                .where(between(ScmCalendar.calendar_date,dt_start,dt_end))\
                .order_by(asc(ScmCalendar.time_id))

            retorno = [{
                    "year": m.year,
                    "month": m.month,
                    "week": m.week
                } for m in db.session.execute(rquery).all()]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_calendar.response(HTTPStatus.OK.value,"Salva um evento no calendário",evt_model)
    @ns_calendar.response(HTTPStatus.BAD_REQUEST.value,"Falha salvar registro!")
    def post(self):
        try:
            req = request.get_json()
            
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }