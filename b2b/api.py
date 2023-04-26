from flask import Blueprint
from flask_restx import Api
from b2b.price_table import ns_price
from b2b.orders import ns_order
from b2b.payment_condition import ns_payment
from b2b.customer_group import ns_group_customer
from b2b.collection import ns_collection
from b2b.brand import ns_brand
from b2b.product_stock import ns_stock
from b2b.cart import ns_cart
from b2b.invoices import ns_invoice

""" Módulo Business to Business (Gestão de Vendas entre empresas)
    Módulo para realizar pedidos que realiza:
        - Gestão de cadastro
            - Clientes
            - Grupos de Clientes
            - Representantes
        - Gestão de pedidos
            - Aprovação/Reprovação
        - Gestão de condições de pagamento
            - Manutenção
        - Gestão de tabelas de preços
            - Manuteção
        - Gestão de produtos
            - Manuteção
            - Configuração
        - Gestão financeira do cliente 
            - Reimpressão/envio de boletos
            - Reimpressão/envio de NF-e

Keyword arguments: vendas, b2c, produtos, cliente, pedidos, condições de pagamento
"""


nss = [ns_brand,
       ns_cart,
       ns_collection,
       ns_group_customer,
       ns_invoice,
       ns_order,
       ns_payment,
       ns_price,   
       ns_stock]

blueprint = Blueprint("b2b",__name__,url_prefix="/b2b/api/")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas - Módulo B2B",
    contact_email="evertonrivas@gmail.com",
    contact="Venda Fashion",
    contact_url="http://www.vendafashion.com")

for ns in nss:
    api.add_namespace(ns)