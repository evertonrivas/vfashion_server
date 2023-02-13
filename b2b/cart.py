from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace

api = Namespace("cart",description="Operações para manipular dados de pedidos de compras (carrinho)")