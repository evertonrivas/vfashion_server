from flask_restx import Api
from flask import Blueprint
from scm.flimv import ns_flimv
from common import _before_execute
from scm.event_type import ns_event
from scm.calendar import ns_calendar
from scm.rep_comission import ns_comission

nss = [ns_calendar,ns_comission,ns_event,ns_flimv]

blueprint = Blueprint("scm",__name__,url_prefix="/scm/api/")
@blueprint.before_request
def before_request():
    """ Executa antes de cada requisição """
    _before_execute()


api = Api(blueprint,
    version="1.0",
    title="API Fast2Bee",
    description="Uma API REST para o sistema CLM - Módulo SCM (Sales Calendar Management)",
    contact_email="e.rivas@fast2bee.com",
    contact="Fast2Bee",
    contact_url="http://www.fast2bee.com")

for ns in nss:
    api.add_namespace(ns)