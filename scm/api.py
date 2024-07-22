from flask import Blueprint
from flask_restx import Api
from scm.calendar import ns_calendar
from scm.event_type import ns_event
from scm.flimv import ns_flimv

nss = [ns_calendar,ns_event,ns_flimv]

blueprint = Blueprint("scm",__name__,url_prefix="/scm/api/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para o sistema CLM - Módulo Sales Calendar Management (SCM)",
    contact_email="e.rivas@fast2bee.com",
    contact="Venda Fashion",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)