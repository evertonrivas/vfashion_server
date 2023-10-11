from http import HTTPStatus
from flask_restx import Resource,fields,Namespace
from flask import request
from models import CrmFunnelStageCustomer, _get_params,CrmFunnelStage,db,_save_log
import json
from sqlalchemy import Select, exc,and_,asc
from auth import auth
from config import Config,CustomerAction


ns_fun_stg = Namespace("funnel-stages",description="Operações para manipular estágios dos funis de clientes")

@ns_fun_stg.route("/<int:id>")
@ns_fun_stg.param("id","Id do registro")
class FunnelStageApi(Resource):
    @ns_fun_stg.response(HTTPStatus.OK.value,"Exibe os dados de um estágio de um funil")
    @ns_fun_stg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            return CrmFunnelStage.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_fun_stg.response(HTTPStatus.OK.value,"Cria ou atualiza um estágio em um funil")
    @ns_fun_stg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_fun_stg.param("id_funnel","Id de registro do funil",required=True,type=int)
    @ns_fun_stg.param("name","Nome do estágio do funil",required=True)
    @ns_fun_stg.param("order","Ordem do estágio dentro do funil",type=int,required=True)
    @auth.login_required
    def post(self,id:int):
        try:
            if id > 0:
                stage = CrmFunnelStage.query.get(id)
                stage.id_funnel = stage.id_funnel if request.form.get("id_funnel") is None else request.form.get("id_funel")
                stage.name  = stage.name if request.form.get("name") is None else request.form.get("name")
                stage.order = stage.order if request.form.get("order") is None else request.form.get("order")
                db.session.commit()
                return stage.id
            else:
                stage = CrmFunnelStage()
                stage.id_funnel = int(request.form.get("id_funnel"))
                stage.name = request.form.get("name")
                stage.order = request.form.get("order")
                db.session.add(stage)
                db.session.commit()
                return stage.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_fun_stg.response(HTTPStatus.OK.value,"Exclui um estágio de um funil")
    @ns_fun_stg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int):
        try:
            stage = CrmFunnelStage.query.get(id)
            db.session.delete(stage)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
class FunnelStageCustomer(Resource):
    @auth.login_required
    def get(self):
        try:
            id_customer = request.args.get("id_customer")
            new_stage   = request.args.get("id_stage")

            customer_stage = CrmFunnelStageCustomer.query.filter(CrmFunnelStageCustomer.id_customer==id_customer).one()
            customer_stage.id_funnel_stage = new_stage
            stage = db.session.execute(Select(CrmFunnelStage.name).where(CrmFunnelStage.id==new_stage)).first().name
            db.session.commit()
            _save_log(id_customer,CustomerAction.MOVE_CRM_FUNNEL,'Movido para o estágio '+stage)

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            for customer in req['customers']:
                customer_state = CrmFunnelStageCustomer.query.filter(CrmFunnelStageCustomer.id_customer==customer.id).one()
                customer_state.id_funnel_stage = req['stage']
                stage = db.session.execute(Select(CrmFunnelStage.name).where(CrmFunnelStage.id==req['stage'])).first().name
                _save_log(customer.id,CustomerAction.MOVE_CRM_FUNNEL,'Movido para o estágio '+stage)
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for customer in req['customers']:
                customer_state = CrmFunnelStageCustomer.query.filter(CrmFunnelStageCustomer.id_customer==customer).one()
                db.session.delete(customer_state)
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
ns_fun_stg.add_resource(FunnelStageCustomer,'/move-customer')

class FunnelStageNotification(Resource):
    def get(self):
        try:
            pass
        except exc.SQLAlchemyError as e:
            pass
    
    def post(self):
        try:
            pass
        except Exception as e:
            pass

    def delete(self):
        try:
            pass
        except exc.SQLAlchemyError as e:
            pass

ns_fun_stg.add_resource(FunnelStageCustomer,'/notification')