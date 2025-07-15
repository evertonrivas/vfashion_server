from flask import Blueprint
from flask_restx import Api
from sys.customer import ns_customer

nss = [ns_customer]

blueprint = Blueprint("scm",__name__,url_prefix="/sys/api/")

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo Sales Calendar Management (SCM)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)