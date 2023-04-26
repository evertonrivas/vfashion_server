from flask import Blueprint
from flask_restx import Api
from crm.funil import ns_funil,ns_fun_stg

""" Módulo Customer Relationship Management (Gestão de Relacionamento com o Cliente). 
    Módulo para gestão de contatos com o cliente (qualificação)

Keyword arguments: relacionamento, clientes, contatos, financeiro
"""

nss = [ns_funil,ns_fun_stg]

blueprint = Blueprint("crm",__name__,url_prefix="/crm/api/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo CRM",
    contact_email="evertonrivas@gmail.com",
    contact="Venda Fashion",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)