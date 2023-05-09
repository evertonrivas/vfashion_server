from flask import Blueprint
from flask_restx import Api
from cmm.users import ns_user
from cmm.products import ns_prod
from cmm.products_grid import ns_gprod
from cmm.products_category import ns_cat
from cmm.products_type import ns_type
from cmm.products_model import ns_model
from cmm.legal_entities import ns_legal
from cmm.translate_colors import ns_color
from cmm.translate_sizes import ns_size
from cmm.countries import ns_country
from cmm.cities import ns_city
from cmm.state_regions import ns_state_region


""" Módulo Common entre os sistemas
    Módulo que unificará os sistemas através de uma única API com coisas que são comuns em todas as etapas

Keyword arguments: usuarios, produtos
"""

#nss = [ns_user]
nss = [ns_cat,ns_city,ns_color,ns_country,ns_gprod,ns_legal,ns_model,ns_prod,ns_size,ns_state_region,ns_type,ns_user]

blueprint = Blueprint("cmm",__name__,url_prefix="/cmm/api/")

api = Api(blueprint,
    version="1.0",
    title="API VFashion",
    description="Uma API REST para o sistema CLM - Módulo Common",
    contact_email="evertonrivas@gmail.com",
    contact="Venda Fashion",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)