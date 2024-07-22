from datetime import datetime
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bBrand, CrmConfig, _get_params,db
import json
from sqlalchemy import Select, exc,and_,asc,desc
from auth import auth

ns_crm_cfg = Namespace("config",description="Configurações do módulo de CRM")

@ns_crm_cfg.route("/")
class CollectionList(Resource):
    @ns_crm_cfg.response(HTTPStatus.OK.value,"Obtem um registro de uma coleção")
    @ns_crm_cfg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
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

    @ns_crm_cfg.response(HTTPStatus.OK.value,"Cria ou atualiza as configurações")
    @ns_crm_cfg.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @auth.login_required
    def post(self)->int:
        try:
            req = request.get_json()
            for k in req:
                cfg_id = db.session.execute(Select(CrmConfig.id).where(CrmConfig.cfg_name==k)).first().id
                cfg:CrmConfig = CrmConfig.query.get(cfg_id)
                cfg.cfg_value = req[k]
                db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }