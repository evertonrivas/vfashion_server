from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,Namespace
from flask import request
from models import CmmProducts,CmmProductsSku,CmmProductsGrid,CmmProductsGridDistribution,db
import sqlalchemy as sa

ns_prod = Namespace("products",description="Operações para manipular dados de produtos")
ns_gprod = Namespace("products-grid",description="Operações para manipular dados das grades de produtos")

####################################################################################
#                INICIO DAS CLASSES QUE IRAO TRATAR OS PRODUTOS.                   #
####################################################################################
@ns_prod.route("/")
class ProductsList(Resource):
    @ns_prod.response(HTTPStatus.OK.value,"Obtem a listagem de produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_prod.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_prod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_prod.param("query","Texto para busca","query")
    def get(self):
        pag_num  =  1 if request.args.get("page")!=None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")!=None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")!=None else "{}%".format(request.args.get("query"))

        if search!="":
            rquery = CmmProducts.query.filter(sa.and_(CmmProducts.trash==False,CmmProducts.name.like(search))).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmProducts.query.filter(CmmProducts.trash==False).paginate(page=pag_num,per_page=pag_size)

        return {
            "paginate":{
                "registers": rquery.total,
                "page": pag_num,
                "per_page": pag_size,
                "pages": rquery.pages,
                "has_next": rquery.has_next
            },
            "data":[{
                "id": m.id,
                "prodCode": m.prodCode,
                "barCode": m.barCode,
                "refCode": m.refCode,
                "name": m.Name,
                "description": m.description,
                "observation": m.observation,
                "ncm": m.ncm,
                "image": m.image,
                "price": m.price,
                "measure_unit": m.measure_unit,
                "structure": m.structure,
                "sku": self.get_sku(m.id)
            } for m in rquery.items]
        }

    def get_sku(self,id:int):
        rquery = CmmProductsSku.query.filter_by(id_product=id)
        return [{
            "color": m.color,
            "size" : m.size
        }for m in rquery.items]

    @ns_prod.response(HTTPStatus.OK.value,"Cria um novo produto no sistema")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo produto!")
    def post(self)->bool:
        prod = CmmProducts()
        prod.prodCode = request.form.get("prodCode")
        prod.barCode  = request.form.get("barCode")
        prod.refCode  = request.form.get("refCode")
        prod.name     = request.form.get("name")
        prod.description = request.form.get("description")
        prod.observation = request.form.get("observation")
        prod.ncm         = request.form.get("ncm")
        prod.image       = request.form.get("image")
        prod.price       = float(request.form.get("price"))
        prod.measure_unit = request.form.get("measure_unit")
        return False


@ns_prod.route("/<int:id>")
@ns_prod.param("id","Id do registro")
class ProductApi(Resource):

    @ns_prod.response(HTTPStatus.OK.value,"Obtem um registro de produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int):
        return CmmProducts.query.get(id).to_dict()

    @ns_prod.response(HTTPStatus.OK.value,"Salva dados de um produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        try:
            prod = CmmProducts.query.get(id)
            prod.prodCode = request.form.get("prodCode")
            prod.barCode  = request.form.get("barCode")
            prod.refCode  = request.form.get("refCode")
            prod.name     = request.form.get("name")
            prod.description = request.form.get("description")
            prod.observation = request.form.get("observation")
            prod.ncm         = request.form.get("ncm")
            prod.image       = request.form.get("image")
            prod.price       = float(request.form.get("price"))
            prod.measure_unit = request.form.get("measure_unit")
            db.session.add(prod)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_prod.response(HTTPStatus.OK.value,"Exclui os dados de um produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        try:
            prod = CmmProducts.query.get(id)
            prod.trash = True
            db.session.add(prod)
            db.session.commit()
            return True
        except:
            return False

####################################################################################
#           INICIO DAS CLASSES QUE IRAO TRATAR AS GRADES DE  PRODUTOS.             #
####################################################################################

@ns_gprod.route("/")
class GridList(Resource):

    @ns_gprod.response(HTTPStatus.OK.value,"Obtem os registros de grades existentes",)
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_gprod.param("page","Número da página de registros","query",type=int,required=True)
    @ns_gprod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_gprod.param("query","Texto para busca","query")
    def get(self):
        pag_num  =  1 if request.args.get("page")!=None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")!=None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")!=None else "{}%".format(request.args.get("query"))

        if search!="":
            rquery = CmmProductsGrid.query.filter(sa.and_(CmmProductsGrid.trash==False,CmmProductsGrid.name.like(search))).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmProductsGrid.query.filter(CmmProductsGrid.trash==False).paginate(page=pag_num,per_page=pag_size)

        return {
            "pagination":{
                "registers": rquery.total,
                "page": pag_num,
                "per_page": pag_size,
                "pages": rquery.pages,
                "has_next": rquery.has_next
            },
            "data":[{
                "id": m.id,
                "name": m.name,
                "distribution": self.get_grid_distribution(m.id)
            }for m in rquery.items]
        }

    def get_grid_distribution(self,id:int):
        rquery = CmmProductsGridDistribution.query.find_by(id_grid=id)
        return [{
            "size": m.size,
            "color": m.color,
            "value": m.value,
            "is_percent": m.is_percent
        } for m in rquery.items]


    @ns_gprod.response(HTTPStatus.OK.value,"Cria uma nova grade no sistema")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova grade!")
    def post(self)->int:
        try:
            grid = CmmProductsGrid()
            grid.name = request.form.get("name")
            db.session.add(grid)
            db.session.commit()

            for dist in request.form.get("distribution"):
                gridd         = CmmProductsGridDistribution()
                gridd.id_grid = grid.id
                gridd.color   = dist["color"]
                gridd.size    = dist["size"]
                gridd.value   = dist["value"]
                gridd.is_percent = dist["is_percent"]
                db.session.add(gridd)
                db.session.commit()

            return grid.id
        except:
            return 0


@ns_gprod.route("/<int:id>")
@ns_prod.param("id","Id do registro")
class GridApi(Resource):
    @ns_gprod.response(HTTPStatus.OK.value,"Obtem um registro de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def get(self,id:int):
        grid = CmmProductsGrid.query.get(id)
        dist = CmmProductsGridDistribution.query.find_by(id_grid=id)
        return {
            "id": grid.id,
            "name": grid.name,
            "distribuition":[{
                "size": m.size,
                "color": m.color,
                "value": m.value,
                "is_percent": m.is_percent
            } for m in dist.items]
        }

    @ns_gprod.response(HTTPStatus.OK.value,"Salva dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def post(self,id:int)->bool:
        try:
            grid = CmmProductsGrid.query.get(id)
            grid.name = request.form.get("name")
            db.session.add(grid)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_gprod.response(HTTPStatus.OK.value,"Exclui os dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def delete(self,id:int)->bool:
        try:
            grid       = CmmProductsGrid.query.get(id)
            grid.trash = True
            db.session.add(grid)
            db.session.commit()
            return True
        except:
            return False