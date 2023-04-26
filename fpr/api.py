from flask import Blueprint
from flask_restx import Api
#from fpr.funil import api as ns_funil

""" Módulo Finished Product Return (Devolução de Produto acabado). 
    Módulo para gestão de devoluções do cliente

Keyword arguments: devolução, cliente, produto
"""

nss = []

blueprint = Blueprint("fpr",__name__,url_prefix="/fpr/api/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo FPR",
    contact_email="evertonrivas@gmail.com",
    contact="Venda Fashion",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)