from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,reqparse,Namespace
import array

api = Namespace("product",description="Operações para manipular dados de produtos")

#API Models
sku_model = api.model(
    "sku",{
        "color": fields.String,
        "size": fields.String
    }
)

prod_model = api.model(
    "Product",{
        "id": fields.Integer,
        "prodCode": fields.String,
        "barCode": fields.String,
        "refCode": fields.String,
        "name": fields.String,
        "description": fields.String,
        "observation": fields.String,
        "ncm": fields.String,
        "image": fields.String,
        "price": fields.Float,
        "sku": fields.List(fields.Nested(sku_model))
    }
)


class ProductSku(TypedDict):
    color:str
    size: str

class Product(TypedDict):
    id:int
    prodCode:str
    barCode:str
    refCode:str
    name:str
    description:str
    observation:str
    ncm:str
    image:str
    price:float
    sku:list[ProductSku]

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE PRODUTOS.             #
####################################################################################
@api.route("/")
class ProductsList(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem a listagem de produto",[prod_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @api.param("page","Número da página")
    @api.doc(description="Teste de documentacao")
    def get(self)-> list[Product]:

        return [{
            "id":1,
            "prodCode": "10",
            "barCode": "7890000000000",
            "refCode": "BZ10",
            "name": "CALCA JEANS",
            "description": "CALCAS",
            "observation": "nada",
            "ncm": "10000",
            "image": "https://...",
            "price": 107.00,
            "sku":[{
                "color": "#FFFFFF",
                "size": "P"
            },
            {
                "color": "#FFFFFF",
                "size": "M"
            }]
        }]

    @api.response(HTTPStatus.OK.value,"Cria um novo produto no sistema")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo produto!")
    @api.doc(parser=prod_model)
    def post(self)->bool:
        return False


@api.route("/<int:id>")
@api.param("id","Id do registro")
class ProductApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de produto",prod_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->Product:
        return None

    @api.doc(parser=prod_model)
    @api.response(HTTPStatus.OK.value,"Salva dados de um produto")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um produto")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False