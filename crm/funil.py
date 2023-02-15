from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request

api = Namespace("funil",description="Operações para manipular funis de clientes")


cst_funnel_model = api.model(
    "CustomerFunnel",{
        "id": fields.Integer
    }
)

funnel_model = api.model(
    "Funnel",{
        "id": fields.Integer,
        "name": fields.String,
        "customers": fields.List(fields.Nested(cst_funnel_model))
    }
)


class FunnelCustomer(TypedDict):
    id:int

class Funnel(TypedDict):
    id:int
    name:str
    customers: list[FunnelCustomer]


@api.route("/")
class FunnelList(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem a listagem de funis",[funnel_model])
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @api.param("page","Número da página de registros","query",type=int,required=True)
    def get(self)-> list[Funnel]:
        
        return [{
            "id": request.args.get("page"),
            "name": "Funil Teste",
            "customers":[{
                "id": 1
            },
            {
                "id": 2
            }]
        }]

    @api.response(HTTPStatus.OK.value,"Salva os dados de um funil")
    @api.param("name","Nome do funil","formData",required=True)
    def post(self)->int:

        return 0

@api.route("/<int:id>")
class FunnelApi(Resource):
    @api.response(HTTPStatus.OK.value,"Obtem um registro de um funil",funnel_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->Funnel:
        return {
            "id": id,
            "name": "Funil Teste",
            "customers":[{
                "id": 1
            },
            {
                "id": 2
            }]
        }

    @api.response(HTTPStatus.OK.value,"Atualiza dados de um funil")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @api.doc(parser=funnel_model)
    def post(self,id:int)->bool:
        return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um funil")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False