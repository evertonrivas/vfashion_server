from flask import Blueprint
from flask_restx import Api
from crm.funnel import ns_funil
from crm.funnel_stage import ns_fun_stg

""" Módulo Customer Relationship Management (Gestão de Relacionamento com o Cliente). 
    Módulo para gestão de contatos com o cliente (qualificação)

Keyword arguments: relacionamento, clientes, contatos, financeiro
"""

nss = [ns_funil,ns_fun_stg]

blueprint = Blueprint("crm",__name__,url_prefix="/crm/api/")

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo CRM",
    contact_email="evertonrivas@gmail.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)