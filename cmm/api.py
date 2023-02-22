from flask import Blueprint
from flask_restx import Api
from cmm.users import ns_user
from cmm.products import ns_prod
from cmm.products import ns_prodg
from cmm.customers import ns_customer
from cmm.customers import ns_customerg


""" Módulo Common entre os sistemas
    Módulo que unificará os sistemas através de uma única API com coisas que são comuns em todas as etapas

Keyword arguments: usuarios, produtos
"""

nss = [ns_user,ns_prod,ns_prodg,ns_customer,ns_customerg]

blueprint = Blueprint("cmm",__name__,url_prefix="/cmm/api/v1/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo Common",
    contact_email="evertonrivas@gmail.com",
    contact="Venda Fashion",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)