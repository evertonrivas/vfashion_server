from flask import Blueprint
from flask_restx import Api
from smc.customer import ns_customer
from smc.plan import ns_plan

nss = [ns_customer, ns_plan]

blueprint = Blueprint("smc",__name__,url_prefix="/smc/api/")

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema Módulo SCM (System Management Customers)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)