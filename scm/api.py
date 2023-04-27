from flask import Blueprint
from flask_restx import Api

blueprint = Blueprint("scm",__name__,url_prefix="/ccm/api/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo Sales Calendar Management (SCM)",
    contact_email="evertonrivas@gmail.com",
    contact="Venda Fashion",
    contact_url="http://www.vendafashion.com")