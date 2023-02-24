from http import HTTPStatus
from flask_restx import Resource,fields,Namespace
from flask import request
from models import CrmFunnel,CrmFunnelStageCustomer,CrmFunnelStage,db
import sqlalchemy as sa
from auth import auth

ns_funil = Namespace("funnels",description="Operações para manipular funis de clientes")
ns_fun_stg = Namespace("funnel-stages",description="Operações para manipular estágios dos funis de clientes")

fun_pag_model = ns_funil.model(
    "Pagination",{
    
    }
)

fun_stg_model = ns_funil.model(
    "FunnelStage",{
        "id": fields.Integer,
        "name": fields.String,
        "order": fields.Integer,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

fun_model = ns_funil.model(
    "Funnel",{
        "id": fields.Integer,
        "name": fields.String,
        "stages": fields.List(fields.Nested(fun_stg_model)),
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

fun_return = ns_funil.model(
    "FunnelReturn",{
        "pagination": fields.Nested(fun_pag_model),
        "data": fields.List(fields.Nested(fun_model))
    }
)


@ns_funil.route("/")
class FunnelList(Resource):
    @ns_funil.response(HTTPStatus.OK.value,"Obtem a listagem de funis",fun_return)
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_funil.param("page","Número da página de registros","query",type=int,required=True)
    @ns_funil.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_funil.param("query","Texto para busca","query")
    #@auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
    
        if search!="":
            rquery = CrmFunnel.query.filter(sa.and_(CrmFunnel.trash==False,CrmFunnel.name.like(search))).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CrmFunnel.query.filter(CrmFunnel.trash==False).paginate(page=pag_num,per_page=pag_size)
        return {
            "pagination":{
                "registers": rquery.total,
                "page": pag_num,
                "per_page": pag_size,
                "pages": rquery.pages,
                "has_next": rquery.has_next
            },
            "data":[{
                "id": m.id,
                "name": m.name,
                "stages": self.get_stages(m.id),
                "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            } for m in rquery.items]
        }

    def get_stages(self,id:int):
        rquery = CrmFunnelStage.query.filter(CrmFunnelStage.id_funnel==id)
        return [{
            "id": m.id,
            "name": m.name,
            "order": m.order,
            "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
            "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
        } for m in rquery.items]

    @ns_funil.response(HTTPStatus.OK.value,"cria um novo funil")
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo funil!")
    @ns_funil.doc(body=fun_model)
    #@auth.login_required
    def post(self)->int:
        try:
            req = request.get_json()
            fun = CrmFunnel()
            fun.name = req.name
            db.session.add(fun)
            db.session.commit()

            for stg in fun.stages:
                stage = CrmFunnelStage()
                stage.name = stg.name
                stage.id_funnel = fun.id
                stage.order = stg.order
                db.session.add(stage)
                db.session.commit()
            return fun.id
        except:
            return 0

@ns_funil.route("/<int:id>")
@ns_funil.param("id","Id do registro")
class FunnelApi(Resource):
    @ns_funil.response(HTTPStatus.OK.value,"Obtem um registro de um funil",fun_model)
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def get(self,id:int):
        rquery = CrmFunnel.query.get(id)
        squery = CrmFunnelStage.query.filter(CrmFunnelStage.id_funnel==id)
        return {
            "id": rquery.id,
            "name": rquery.name,
            "date_created": rquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
            "date_updated": rquery.date_updated.strftime("%Y-%m-%d %H:%M:%S"),
            "stages": [{
                "id": m.id,
                "name": m.name,
                "order": m.order,
                "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            }for m in squery.items]
        }

    @ns_funil.response(HTTPStatus.OK.value,"Atualiza dados de um funil")
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_funil.param("name","Nome do funil",required=True)
    #@auth.login_required
    def post(self,id:int)->bool:
        try:
            fun = CrmFunnel.query.get(id)
            fun.name = fun.name if request.form.get("name") is None else request.form.get("name")
            db.session.commit()
        except:
            return False
    
    @ns_funil.response(HTTPStatus.OK.value,"Exclui os dados de um funil")
    @ns_funil.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def delete(self,id:int)->bool:
        try:
            fun = CrmFunnel.query.get(id)
            fun.trash = True
            db.session.commit()
            return True
        except:
            return False
        
@ns_fun_stg.route("/<int:id>")
@ns_fun_stg.param("id","Id do registro")
class FunnelStageApi(Resource):
    @ns_fun_stg.response(HTTPStatus.OK.value,"Exibe os dados de um estágio de um funil")
    @ns_fun_stg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def get(self,id:int):
        return CrmFunnelStage.query.get(id).to_dict()

    @ns_fun_stg.response(HTTPStatus.OK.value,"Cria ou atualiza um estágio em um funil")
    @ns_fun_stg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_fun_stg.param("id_funnel","Id de registro do funil",required=True,type=int)
    @ns_fun_stg.param("name","Nome do estágio do funil",required=True)
    @ns_fun_stg.param("order","Ordem do estágio dentro do funil",type=int,required=True)
    #@auth.login_required
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
        except:
            return 0

    @ns_fun_stg.response(HTTPStatus.OK.value,"Exclui um estágio de um funil")
    @ns_fun_stg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def delete(self,id:int):
        try:
            stage = CrmFunnelStage.query.get(id)
            db.session.delete(stage)
            db.session.commit()
            return True
        except:
            return False