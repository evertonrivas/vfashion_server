from flask_restx import Api
from models.public import SysUsers
from models.helpers import Database
from flask import Blueprint, request
# from pos.consumer import api as ns_consumer
# from pos.consumer import apis as ns_consumer_group


# nss = [ns_consumer,ns_consumer_group]

blueprint = Blueprint("mpg",__name__,url_prefix="/mpg/api/")

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
    description="Uma API REST para o sistema CLM - Módulo MPG (Marketing Plan Generator)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

# for ns in nss:
#     api.add_namespace(ns)