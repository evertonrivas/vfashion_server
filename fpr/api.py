from flask_restx import Api
from fpr.reasons import ns_reason
from flask import Blueprint, request
from models.helpers import Database
from fpr.devolution import ns_devolution

""" Módulo Finished Product Return (Devolução de Produto acabado). 
    Módulo para gestão de devoluções do cliente

Keyword arguments: devolução, cliente, produto
"""

nss = [ns_reason, ns_devolution]

blueprint = Blueprint("fpr",__name__,url_prefix="/fpr/api/")
@blueprint.before_request
def before_request():
    """ Executa antes de cada requisição """
    if request.headers.get("x-customer", None) is None:
        return {"message": "Customer header is required"}, 400
    
    tenant = Database(str(request.headers.get("tenant")))
    tenant.switch_schema()

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo FPR (Finished Product Return)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)