from flask import Blueprint
from flask_restx import Api
from b2b.cart import ns_cart
from b2b.orders import ns_order
from b2b.payment_condition import ns_payment


nss = [ns_cart,ns_order,ns_payment]

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