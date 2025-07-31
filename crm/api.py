from flask import Blueprint
from flask_restx import Api
from crm.funnel import ns_funil
from crm.config import ns_crm_cfg
from common import _before_execute
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
    _before_execute()

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo CRM (Customer Relashionship Management)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)