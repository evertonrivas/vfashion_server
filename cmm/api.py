from flask import Blueprint
from flask_restx import Api
from cmm.users import api as ns_user
from cmm.products import api as ns_product
from cmm.customers import api as ns_customer
from cmm.customers import apis as ns_group_group

""" Módulo Common entre os sistemas
    Módulo que unificará os sistemas através de uma única API com coisas que são comuns em todas as etapas

Keyword arguments: usuarios, produtos
"""


nss = [ns_user,ns_product,ns_customer,ns_group_group]

blueprint = Blueprint("cmm",__name__,url_prefix="/cmm/api/v1/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo Common",
    contact_email="evertonrivas@gmail.com",
    contact="Venda",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)