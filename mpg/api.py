from flask_restx import Api
from flask import Blueprint
from common import _before_execute
# from pos.consumer import api as ns_consumer
# from pos.consumer import apis as ns_consumer_group


# nss = [ns_consumer,ns_consumer_group]

bp_mpg = Blueprint("mpg",__name__,url_prefix="/mpg/api/")

@bp_mpg.before_request
def before_request():
    """ Executa antes de cada requisição """
    _before_execute()

api = Api(bp_mpg,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo MPG (Marketing Plan Generator)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

# for ns in nss:
#     api.add_namespace(ns)