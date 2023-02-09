from flask import Blueprint
from flask_restx import Api
from sfm.users import api as ns_user
from sfm.customers import api as ns_customer
from sfm.customers import apis as ns_group
from sfm.orders import api as ns_order
from sfm.products import api as ns_product


nss = [ns_user,ns_customer,ns_group,ns_order,ns_product]


blueprint = Blueprint("sfm",__name__,url_prefix="/sfm/api/v1/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas",
    contact_email="evertonrivas@gmail.com",
    contact="Venda",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)