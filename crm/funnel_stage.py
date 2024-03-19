from http import HTTPStatus
from flask_restx import Resource,fields,Namespace
from flask import request
from models import CrmFunnel, CrmFunnelStageCustomer, _get_params,CrmFunnelStage,db,_save_log
import json
from sqlalchemy import Select, desc, exc,and_,asc, or_
from auth import auth
from config import Config,CustomerAction


ns_fun_stg = Namespace("funnel-stages",description="Operações para manipular estágios dos funis de clientes")

@ns_fun_stg.route("/")
class FunnelStagesApi(Resource):
    @ns_fun_stg.response(HTTPStatus.OK.value,"Exibe os dados de um estágio de um funil")
    @ns_fun_stg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_fun_stg.param("page","Número da página de registros","query",type=int,required=True)
    @ns_fun_stg.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_fun_stg.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else request.args.get("query")
        try:
            params    = _get_params(query)
            trash     = False if hasattr(params,'trash')==False else True
            list_all  = False if hasattr(params,"list_all")==False else True
            order_by  = "id" if hasattr(params,"order_by")==False else params.order_by
            direction = desc if hasattr(params,"order_dir") == 'DESC' else asc

            filter_search = None if hasattr(params,"search")==False or params.search=="" else params.search

            rquery = Select(CrmFunnelStage.id,
                            CrmFunnelStage.id_funnel,
                            CrmFunnel.name.label("funnel"),
                            CrmFunnelStage.name,
                            CrmFunnelStage.icon,
                            CrmFunnelStage.color,
                            CrmFunnelStage.order,
                            CrmFunnelStage.date_created,
                            CrmFunnelStage.date_updated)\
                            .join(CrmFunnel,CrmFunnel.id==CrmFunnelStage.id_funnel)\
                            .where(CrmFunnelStage.trash==trash)\
                            .order_by(direction(getattr(CrmFunnelStage,order_by)))
            
            if filter_search is not None:
                rquery = rquery.where(or_(
                    CrmFunnelStage.name.like("%{}%".format(filter_search)),
                    CrmFunnel.name.like("%{}%".format(filter_search))
                ))
            
            if list_all==False:
                pag    = db.paginate(rquery,page=pag_num,per_page=pag_size)
                rquery = rquery.limit(pag_size).offset((pag_num - 1) * pag_size)
                return {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next
                    },
                    "data":[{
                        "id": m.id,
                        "id_funel":m.id_funnel,
                        "funnel": m.funnel,
                        "name": m.name,
                        "icon": m.icon,
                        "color": m.color,
                        "order": m.order,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    }for m in db.session.execute(rquery)]
                }
            else:
                return [{
                        "id": m.id,
                        "id_funel":m.id_funnel,
                        "funnel": m.funnel,
                        "name": m.name,
                        "icon": m.icon,
                        "color": m.color,
                        "order": m.order,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    }for m in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return{
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @auth.login_required
    def post(self):
        try:
            pass
        except exc.SQLAlchemyError as e:
            return{
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

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