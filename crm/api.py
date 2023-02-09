from flask import Blueprint
from flask_restx import Api
from crm.opportunities import api as ns_opportunity

""" Módulo Customer Relationship Management (Gestão de Relacionamento com o Cliente). 
    Módulo para gestão de contatos com o cliente incluindo vida financeira (emissão de boletos, 2ª via NF-e, qualificação)

Keyword arguments: relacionamento, clientes, contatos, financeiro
"""

nss = [ns_opportunity]

blueprint = Blueprint("crm",__name__,url_prefix="/crm/api/v1/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo CRM",
    contact_email="evertonrivas@gmail.com",
    contact="Venda",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)