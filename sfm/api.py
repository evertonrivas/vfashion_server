from flask import Blueprint
from flask_restx import Api
from sfm.orders import api as ns_order

""" Módulo Sales Force Management (Gestão de Força de Vendas). 
    Basicamente é um módulo para realização de pedidos e também aprovação de pedidos.

Keyword arguments: pedidos, clientes, produtos
"""


nss = [ns_order]


blueprint = Blueprint("sfm",__name__,url_prefix="/sfm/api/v1/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo SFM",
    contact_email="evertonrivas@gmail.com",
    contact="Venda",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)