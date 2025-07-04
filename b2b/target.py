from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bTarget, db
# from models import _show_query
from sqlalchemy import Select, Update, exc, func
from auth import auth

ns_target = Namespace("target",description="Operações para manipular dados de metas")

target_model = ns_target.model(
    "Target",{
        "id": fields.Integer,
        "type": fields.String,
        "year": fields.Integer,
        "max_value": fields.Float,
        "value_year": fields.Float,
        "value_quarter1": fields.Float,
        "value_quarter2": fields.Float,
        "value_quarter3": fields.Float,
        "value_quarter4": fields.Float,
        "value_jan": fields.Float,
        "value_feb": fields.Float,
        "value_mar": fields.Float,
        "value_apr": fields.Float,
        "value_may": fields.Float,
        "value_jun": fields.Float,
        "value_jul": fields.Float,
        "value_aug": fields.Float,
        "value_sep": fields.Float,
        "value_oct": fields.Float,
        "value_nov": fields.Float,
        "value_dec": fields.Float,
    }
)

@ns_target.route("/<int:year>")
class CollectionList(Resource):
    @ns_target.response(HTTPStatus.OK.value,"Obtem um registro de metas de um ano",target_model)
    @ns_target.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,year:int):
        try:
            target = db.session.execute(Select(B2bTarget.id,
                            B2bTarget.type,
                            B2bTarget.year,
                            B2bTarget.max_value,
                            B2bTarget.value_year,
                            B2bTarget.value_quarter1,
                            B2bTarget.value_quarter2,
                            B2bTarget.value_quarter3,
                            B2bTarget.value_quarter4,
                            B2bTarget.value_jan,
                            B2bTarget.value_feb,
                            B2bTarget.value_mar,
                            B2bTarget.value_apr,
                            B2bTarget.value_may,
                            B2bTarget.value_jun,
                            B2bTarget.value_jul,
                            B2bTarget.value_aug,
                            B2bTarget.value_sep,
                            B2bTarget.value_oct,
                            B2bTarget.value_nov,
                            B2bTarget.value_dec)\
                            .where(B2bTarget.year==year)).first()
            
            if target is not None:
                return {
                    "id": target.id,
                    "type": target.type,
                    "year": target.year,
                    "max_value": str(target.max_value),
                    "value_year": str(target.value_year),
                    "value_quarter1": str(target.value_quarter1),
                    "value_quarter2": str(target.value_quarter2),
                    "value_quarter3": str(target.value_quarter3),
                    "value_quarter4": str(target.value_quarter4),
                    "value_jan": str(target.value_jan),
                    "value_feb": str(target.value_feb),
                    "value_mar": str(target.value_mar),
                    "value_apr": str(target.value_apr),
                    "value_may": str(target.value_may),
                    "value_jun": str(target.value_jun),
                    "value_jul": str(target.value_jul),
                    "value_aug": str(target.value_aug),
                    "value_sep": str(target.value_sep),
                    "value_oct": str(target.value_oct),
                    "value_nov": str(target.value_nov),
                    "value_dec": str(target.value_dec)
                    }
            return None
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_target.response(HTTPStatus.OK.value,"Cria ou atualiza metas do ano")
    @ns_target.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_target.doc(body=target_model)
    @auth.login_required
    def post(self,year:int)->bool|dict:
        try:
            req = request.get_json()

            exist = db.session.execute(Select(func.count(B2bTarget.id).label("total")).where(B2bTarget.year==year)).first().total
            if exist == 0:
                target = B2bTarget()
                target.year = year
                target.type           = req["type"]
                target.max_value      = req["max_value"]
                target.value_year     = req["value_year"]
                target.value_quarter1 = req["value_quarter1"]
                target.value_quarter2 = req["value_quarter2"]
                target.value_quarter3 = req["value_quarter3"]
                target.value_quarter4 = req["value_quarter4"]
                target.value_jan      = req["value_jan"]
                target.value_feb      = req["value_feb"]
                target.value_mar      = req["value_mar"]
                target.value_apr      = req["value_apr"]
                target.value_may      = req["value_may"]
                target.value_jun      = req["value_jun"]
                target.value_jul      = req["value_jul"]
                target.value_aug      = req["value_aug"]
                target.value_sep      = req["value_sep"]
                target.value_oct      = req["value_oct"]
                target.value_nov      = req["value_nov"]
                target.value_dec      = req["value_dec"]
                db.session.add(target)
            else:
                db.session.execute(
                    Update(B2bTarget).values(
                        { "type": req["type"],
                        "max_value": req["max_value"],
                        "value_year": req["value_year"],
                        "value_quarter1": req["value_quarter1"],
                        "value_quarter2": req["value_quarter2"],
                        "value_quarter3": req["value_quarter3"],
                        "value_quarter4": req["value_quarter4"],
                        "value_jan": req["value_jan"],
                        "value_feb": req["value_feb"],
                        "value_mar": req["value_mar"],
                        "value_apr": req["value_apr"],
                        "value_may": req["value_may"],
                        "value_jun": req["value_jun"],
                        "value_jul": req["value_jul"],
                        "value_aug": req["value_aug"],
                        "value_sep": req["value_sep"],
                        "value_oct": req["value_oct"],
                        "value_nov": req["value_nov"],
                        "value_dec": req["value_dec"]}
                    ).where(B2bTarget.year==year)
                )
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }