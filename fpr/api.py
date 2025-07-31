from flask_restx import Api
from flask import Blueprint
from fpr.reasons import ns_reason
from common import _before_execute
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
    _before_execute()

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo FPR (Finished Product Return)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)