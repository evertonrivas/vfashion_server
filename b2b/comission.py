from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bComissionRepresentative, db
# from models import _show_query
from sqlalchemy import Select, Update, and_, exc, func
from auth import auth

ns_comission = Namespace("comission",description="Operações para manipular dados de comissoes")

comission_model = ns_comission.model(
    "Comission",{
        "id": fields.Integer,
        "id_representative": fields.String,
        "year": fields.Integer,
        "percent": fields.Float,
        "value": fields.Float
    }
)

comission_return = fields.List(fields.Nested(comission_model))

@ns_comission.route("/<int:year>")
class ComissionList(Resource):
    @ns_comission.response(HTTPStatus.OK.value,"Obtem um registro de comissoes de um ano",comission_return)
    @ns_comission.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,year:int):
        try:
            comission = Select(
                B2bComissionRepresentative.id,
                B2bComissionRepresentative.id_representative,
                B2bComissionRepresentative.percent,
                B2bComissionRepresentative.value)\
                .where(B2bComissionRepresentative.year==year)
            return {
            "year": year,
            "comission": [{
                "id": c.id,
                "id_representative": c.id_representative,
                "percent": str(c.percent),
                "value": str(c.value)
                }for c in db.session.execute(comission)]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_comission.response(HTTPStatus.OK.value,"Cria ou atualiza uma nova comissao do ano")
    @ns_comission.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_comission.doc(body=comission_model)
    @auth.login_required
    def post(self,year:int)->bool|dict:
        try:
            req = request.get_json()

            exist = db.session.execute(Select(func.count(B2bComissionRepresentative.id).label("total")).where(B2bComissionRepresentative.year==year)).first().total
            if exist == 0:
                for com in req:
                    comission = B2bComissionRepresentative()
                    comission.id_representative = com["id_representative"]
                    comission.year    = year
                    comission.percent = com["percent"]
                    comission.value   = 0
                    db.session.add(comission)
                db.session.commit()
            else:
                for com in req:
                    comission = db.session.execute(
                        Update(B2bComissionRepresentative).values(percent=com["percent"]).where(
                            and_(
                                B2bComissionRepresentative.year==year,
                                B2bComissionRepresentative.id_representative==com["id_representative"]
                            )
                        )
                    )
                    db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }