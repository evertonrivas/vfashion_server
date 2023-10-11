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
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo FPR",
    contact_email="evertonrivas@gmail.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)