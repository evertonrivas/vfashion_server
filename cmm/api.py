from flask import Blueprint, request
from cmm.ai import ns_ai
from flask_restx import Api
from cmm.users import ns_user
from cmm.cities import ns_city
from cmm.email import ns_email
from cmm.products import ns_prod
from cmm.upload import ns_upload
from cmm.config import ns_config
from cmm.reports import ns_report
from models.helpers import Database
from cmm.countries import ns_country
from cmm.products_type import ns_type
from cmm.products_grid import ns_gprod
from cmm.translate_sizes import ns_size
from cmm.products_model import ns_model
from cmm.legal_entities import ns_legal
from cmm.products_category import ns_cat
from cmm.translate_colors import ns_color
from cmm.state_regions import ns_state_region
from cmm.measure_unit import ns_measure_unit


""" Módulo Common entre os sistemas
    Módulo que unificará os sistemas através de uma única API com coisas que são comuns em todas as etapas

Keyword arguments: usuarios, produtos
"""

#nss = [ns_user]
nss = [ns_ai,
       ns_cat,
       ns_city,
       ns_color,
       ns_config,
       ns_country,
       ns_gprod,
       ns_legal,
       ns_measure_unit,
       ns_model,
       ns_prod,
       ns_report,
       ns_size,
       ns_state_region,
       ns_type,
       ns_upload,
       ns_user,
       ns_email
    ]


blueprint = Blueprint("cmm",__name__,url_prefix="/cmm/api/")
@blueprint.before_request
def before_request():
    """ Executa antes de cada requisição """
    if request.headers.get("x-customer", None) is None:
        return {"message": "Customer header is required"}, 400
    
    tenant = Database(str(request.headers.get("tenant")))
    tenant.switch_schema()

api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM (Módulo Common)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)