from flask_restx import Api
from crm.funnel import ns_funil
from crm.config import ns_crm_cfg
from models.public import SysUsers
from models.helpers import Database
from flask import Blueprint, request
from crm.funnel_stage import ns_fun_stg

""" Módulo Customer Relationship Management (Gestão de Relacionamento com o Cliente). 
    Módulo para gestão de contatos com o cliente (qualificação)

Keyword arguments: relacionamento, clientes, contatos, financeiro
"""

nss = [ns_funil,ns_fun_stg,ns_crm_cfg]

blueprint = Blueprint("crm",__name__,url_prefix="/crm/api/")

@blueprint.before_request
def before_request():
    """ Executa antes de cada requisição """
    if "Authorization" in request.headers:
        tkn = request.headers["Authorization"].replace("Bearer ","")
        if tkn is not None:
            token = SysUsers.extract_token(tkn) if tkn else None
            tenant = Database(str('' if token is None else token["profile"]))
            tenant.switch_schema()

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo CRM (Customer Relashionship Management)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)