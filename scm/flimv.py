from auth import auth
from flask import request
from http import HTTPStatus
from datetime import datetime
from models.helpers import db
from models.tenant import ScmFlimv
from sqlalchemy import Select, exc, desc
from flask_restx import Resource, Namespace, fields

ns_flimv = Namespace("flimv",description="Operações para manipular dados da metodologia FLIMV")

flimv_pag_model = ns_flimv.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

flimv_model = ns_flimv.model(
    "EventType",{
        "id": fields.Integer,
        "name": fields.String,
        "hex_color": fields.String,
        "has_budget": fields.Boolean,
        "use_collection": fields.Boolean
    }
)

event_return = ns_flimv.model(
    "BrandReturn",{
        "pagination": fields.Nested(flimv_pag_model),
        "data": fields.List(fields.Nested(flimv_model))
    }
)

@ns_flimv.route("/")
class FlimvList(Resource):
    @ns_flimv.response(HTTPStatus.OK,"Obtem a listagem de flimvs")
    @ns_flimv.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_flimv.param("id","Id para busca de um registro","query",type=int,required=False)
    @auth.login_required
    def get(self):
        id = None if request.args.get("id") is None else request.args.get("id")
        try:
            if id is None:
                flimvs = Select(ScmFlimv.id,
                                ScmFlimv.frequency,
                                ScmFlimv.liquidity,
                                ScmFlimv.injury,
                                ScmFlimv.mix,
                                ScmFlimv.vol_min,
                                ScmFlimv.vol_max).order_by(desc(ScmFlimv.id))
                return [{
                    "id": f.id,
                    "frequency": f.frequency,
                    "liquidity": f.liquidity,
                    "injury": f.injury,
                    "mix": f.mix,
                    "volume": [f.vol_min,f.vol_max]
                }for f in db.session.execute(flimvs)]
            else:
                flimv:ScmFlimv|None = ScmFlimv.query.get(id)
                if flimv is None:
                    return {"error":"Registro não encontrado!"}, HTTPStatus.BAD_REQUEST

            return {
                "id": flimv.id,
                "frequency": flimv.frequency,
                "liquidity": flimv.liquidity,
                "injury": flimv.injury,
                "mix": flimv.mix,
                "volume": [flimv.vol_min,flimv.vol_max]
            }

        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_flimv.response(HTTPStatus.OK,"Salva ou atualiza um flimv")
    @ns_flimv.response(HTTPStatus.BAD_REQUEST,"Falha ao salvar ou atualizar registro!")
    @auth.login_required
    def post(self):
        req = request.get_json()
        try:
            # print(req)
            for rule in req["rules"]:
                flimv = ScmFlimv.query.get(int(rule["id"]))
                if flimv is not None:
                    flimv.frequency = rule["frequency"]
                    flimv.liquidity = rule["liquidity"]
                    flimv.injury    = rule["injury"]
                    flimv.mix       = rule["mix"]
                    flimv.vol_min   = rule["volume"][0]
                    flimv.vol_max   = rule["volume"][1]
                    flimv.date_updated = datetime.now()
                    db.session.commit()
                else:
                    flimv = ScmFlimv()
                    flimv.frequency = rule["frequency"]
                    flimv.liquidity = rule["liquidity"]
                    flimv.injury    = rule["injury"]
                    flimv.mix       = rule["mix"]
                    flimv.vol_min   = rule["volume"][0]
                    flimv.vol_max   = rule["volume"][1]
                    db.session.add(flimv)
                    db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }