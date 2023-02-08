from flask import Blueprint
from flask_restx import Api

blueprint = Blueprint("api",__name__,url_prefix="/api/v1")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas",
    contact_email="evertonrivas@gmail.com",
    contact="Venda Fashion",
    contact_url="http://www.vendafashion.com")

ns_user = api.namespace("users",description="Operações para manipular dados de usuários do sistema")
api.add_namespace(ns_user)

ns_rep = api.namespace("representatives",description="Operações para manipular dados de representantes")
api.add_namespace(ns_rep)

import users
import representatives