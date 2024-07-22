from flask import Blueprint
from flask_restx import Api
# from pos.consumer import api as ns_consumer
# from pos.consumer import apis as ns_consumer_group


# nss = [ns_consumer,ns_consumer_group]

blueprint = Blueprint("mpg",__name__,url_prefix="/mpg/api/")

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo MPG",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

# for ns in nss:
#     api.add_namespace(ns)