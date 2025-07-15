import json
from auth import auth
from flask import request
from http import HTTPStatus
from models.helpers import db
from sqlalchemy import Select, exc
from models.tenant import CrmConfig
from flask_restx import Resource,Namespace

ns_crm_cfg = Namespace("config",description="Configurações do módulo de CRM")

@ns_crm_cfg.route("/")
class CollectionList(Resource):
    @ns_crm_cfg.response(HTTPStatus.OK,"Obtem um registro de uma coleção")
    @ns_crm_cfg.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self):
        try:
            stmt = Select(CrmConfig.cfg_name,CrmConfig.cfg_value)

            config_str = ""
            configs = []
            for cfg in db.session.execute(stmt):
                configs.append('"'+cfg.cfg_name+'":"'+cfg.cfg_value+'"')

            config_str = "{" + ','.join(configs)+"}"

            return json.loads(config_str)
                
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_crm_cfg.response(HTTPStatus.OK,"Cria ou atualiza as configurações")
    @ns_crm_cfg.response(HTTPStatus.BAD_REQUEST,"Falha ao criar registro!")
    @auth.login_required
    def post(self)->int|dict:
        try:
            req = request.get_json()
            for k in req:
                cfg_id = db.session.execute(Select(CrmConfig.id).where(CrmConfig.cfg_name==k)).first()
                cfg:CrmConfig|None = CrmConfig.query.get(cfg_id.id if cfg_id is not None else 0)
                if cfg is not None:
                    cfg.cfg_value = req[k]
                    db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }