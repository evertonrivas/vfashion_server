from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace

ns_cart = Namespace("cart",description="Operações para manipular dados de pedidos de compras (carrinho)")