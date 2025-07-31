from flask import Blueprint
from flask_restx import Api
from smc.plan import ns_plan
from smc.customer import ns_customer
from smc.payment import ns_payment
from smc.users import ns_user

nss = [ns_customer, ns_plan, ns_payment, ns_user]

blueprint = Blueprint("smc",__name__,url_prefix="/smc/api/")

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema Módulo SMC (System Management Customers)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)