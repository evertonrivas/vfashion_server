from flask import Blueprint
from flask_restx import Api
from cmm.users import ns_user
from cmm.products import ns_prod
from cmm.products_grid import ns_gprod
from cmm.products_category import ns_cat
from cmm.products_type import ns_type
from cmm.products_model import ns_model
from cmm.legal_entities import ns_legal


""" Módulo Common entre os sistemas
    Módulo que unificará os sistemas através de uma única API com coisas que são comuns em todas as etapas

Keyword arguments: usuarios, produtos
"""

#nss = [ns_user]
nss = [ns_prod,ns_gprod,ns_cat,ns_user,ns_legal,ns_type,ns_model]

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