from flask import Blueprint
from flask_restx import Api
from b2b.cart import api as ns_cart


nss = [ns_cart]

blueprint = Blueprint("b2b",__name__,url_prefix="/b2b/api/v1/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo B2B",
    contact_email="evertonrivas@gmail.com",
    contact="Venda Fashion",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)