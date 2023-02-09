from flask import Blueprint
from flask_restx import Api
from sfm.users import api as ns_user
from sfm.customers import api as ns_customer
from sfm.customers import apis as ns_group

blueprint = Blueprint("sfm",__name__,url_prefix="/sfm/api/v1/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas",
    contact_email="evertonrivas@gmail.com",
    contact="Venda",
    contact_url="http://www.vendafashion.com")

api.add_namespace(ns_user)
api.add_namespace(ns_customer)
api.add_namespace(ns_group)