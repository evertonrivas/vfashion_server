from flask_restx import Api
from fpr.reasons import ns_reason
from models.public import SysUsers
from models.helpers import Database
from flask import Blueprint, request
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
    if "Authorization" in request.headers:
        tkn = request.headers["Authorization"].replace("Bearer ","")
        if tkn is not None:
            token = SysUsers.extract_token(tkn) if tkn else None
            tenant = Database(str('' if token is None else token["profile"]))
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