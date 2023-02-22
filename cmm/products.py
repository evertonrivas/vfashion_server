from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request
from models import CmmProducts,CmmProductsSku,CmmProductGrid,CmmProductGridDistribution,db
import sqlalchemy as sa

ns_prod  = Namespace("products",description="Operações para manipular dados de produtos")
ns_prodg = Namespace("products-grid",description="Operações para manipular dados das grades de produtos")

#API Models
prd_pag_model = ns_prod.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

prd_sku_model = ns_prod.model(
    "SKU",{
        "color": fields.String,
        "size": fields.String
    }
)

prd_model = ns_prod.model(
    "Product",{
        "id": fields.Integer,
        "idcategory": fields.Integer,
        "prodCode": fields.String,
        "barCode": fields.String,
        "refCode": fields.String,
        "name": fields.String,
        "description": fields.String,
        "observation": fields.String,
        "ncm": fields.String,
        "image": fields.String,
        "price": fields.Float,
        "measure_unit": fields.String,
        "structure": fields.String,
        "sku": fields.List(fields.Nested(prd_sku_model))
    }
)

prd_return = ns_prod.model(
    "ProductReturn",{
        "pagination": fields.Nested(prd_pag_model),
        "data":fields.List(fields.Nested(prd_model))
    }
)

####################################################################################
#                INICIO DAS CLASSES QUE IRAO TRATAR OS PRODUTOS.                   #
####################################################################################
@ns_prod.route("/")
class ProductsList(Resource):
    @ns_prod.response(HTTPStatus.OK.value,"Obtem a listagem de produto",prd_return)
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_prod.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_prod.param("pageSize","Número de registros da página (máximo: 200)",type=int,required=True,default=25)
    @ns_prod.param("query","Texto a ser buscado")
    def get(self):
        pag_num  = 1 if request.args.get("page")==None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")==None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")==None else "{}%".format(request.args.get("search"))

        if search == "":
            rquery = CmmProducts.query.filter(CmmProducts.trash==False).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmProducts.query.filter(sa.and_(CmmProducts.trash==False,CmmProducts.name.like(search))).paginate(page=pag_num,per_page=pag_size)

        return {
            "pagination":{
                "registers": rquery.total,
                "page": pag_num,
                "per_page": pag_size,
                "pages": rquery.pages,
                "has_next": rquery.has_next
            },
            "data":[{
                "id":m.id,
                "prodCode": m.prodCode,
                "barCode": m.barCode,
                "refCode": m.refCode,
                "name": m.name,
                "description": m.description,
                "observation": m.observation,
                "ncm": m.ncm,
                "image": m.image,
                "price": m.price,
                "measure_unit": m.measure_unit,
                "structure": m.structure,
                "sku":self.get_sku(m.id),
                "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            } for m in rquery.items]
        }

    def get_sku(self,id:int):
        rquery = CmmProductsSku.query.filter(CmmProductsSku.id_product==id)
        return [{
            "size": m.size,
            "color": m.color
        }for m in rquery.items]

    @ns_prod.response(HTTPStatus.OK.value,"Cria um novo produto no sistema")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo produto!")
    @ns_prod.doc(parser=prd_model)
    def post(self)->int:
        try:
            req = request.get_json("product")
            
            prod = CmmProducts()
            prod.prodCode = req.prodCode
            prod.barCode  = req.barCode
            prod.refCode  = req.refCode
            prod.name     = req.name
            prod.description = req.description
            prod.observation = req.observation
            prod.ncm    = req.ncm
            prod.image  = req.image
            prod.price  = req.price
            prod.measure_unit = req.measure_unit
            prod.structure = req.structure
            db.session.add(prod)
            db.session.commit()

            for sku in prod.sku:
                sprod = CmmProductsSku()
                sprod.id_product = prod.id
                sprod.size = sku.size
                sprod.color = sku.color
                db.session.add(sprod)
                db.session.commit()

            return prod.id
        except:
            return 0


@ns_prod.route("/<int:id>")
@ns_prod.param("id","Id do registro")
class ProductApi(Resource):

    @ns_prod.response(HTTPStatus.OK.value,"Obtem um registro de produto",prd_model)
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int):
        return CmmProducts.query.get(id).to_dict()

    @ns_prod.response(HTTPStatus.OK.value,"Salva dados de um produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_prod.doc(parser=prd_model)
    def post(self,id:int)->bool:
        try:
            req = request.get_json("product")
            prod = CmmProducts.query.get(id)
            prod.prodCode = prod.prodCode if req.prodCode==None else req.prodCode
            prod.barCode  = prod.barCode if req.barCode==None else req.barCode
            prod.refCode  = prod.refCode if req.refCode==None else req.refCoe
            prod.name     = prod.name if req.name==None else req.name
            prod.description = prod.description if req.description==None else req.description
            prod.observation = prod.observation if req.observation==None else req.description
            prod.ncm    = prod.ncm if req.ncm==None else req.ncm
            prod.image  = prod.image if req.image==None else req.image
            prod.price  = prod.price if req.price==None else req.price
            prod.measure_unit = prod.measure_unit if req.measure_unit==None else req.measure_unit
            prod.structure = prod.structure if req.structure==None else req.structure
            db.session.add(prod)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_prod.response(HTTPStatus.OK.value,"Exclui os dados de um produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        return False

####################################################################################
#           INICIO DAS CLASSES QUE IRAO TRATAR AS GRADES DE  PRODUTOS.             #
####################################################################################

grd_pag_model = ns_prodg.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

dist_model = ns_prodg.model(
    "GridDistribution",{
        "id_grid": fields.Integer,
        "size": fields.Integer,
        "color": fields.String,
        "value": fields.Float,
        "is_percent":fields.Boolean
    }
)

grid_model = ns_prodg.model(
    "Grid",{
        "id":fields.Integer,
        "name": fields.String,
        "distribution": fields.List(fields.Nested(dist_model))
    }
)

grd_return = ns_prodg.model(
    "GridReturn",{
        "Pagination": fields.Nested(grd_pag_model),
        "data": fields.List(fields.Nested(grid_model))
    }
)

@ns_prodg.route("/")
class GridList(Resource):

    @ns_prodg.response(HTTPStatus.OK.value,"Obtem os registros de grades existentes",grd_return)
    @ns_prodg.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_prodg.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_prodg.param("pageSize","Número de registros da página (máximo: 200)",type=int,required=True,default=25)
    @ns_prodg.param("query","Texto a ser buscado")
    def get(self):
        pag_num  = 1 if request.args.get("page")==None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")==None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")==None else "{}%".format(request.args.get("search")) 

        if search=="":
            rquery = CmmProductGrid.query.filter(CmmProductGrid.trash==False).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmProductGrid.query.filter(sa.and_(CmmProductGrid.trash==False,CmmProductGrid.name.like(search))).paginate(page=pag_num,per_page=pag_size)
        return {
            "pagination":{
                "registers": rquery.total,
                "page": pag_num,
                "per_page": pag_size,
                "pages": rquery.pages,
                "has_next": rquery.has_next
            },"data":[{
                "id":m.id,
                "name":m.name,
                "distribution": self.get_distribution(m.id)
            } for m in rquery.items]
        }

    def get_distribution(self,id:int):
        rquery = CmmProductGridDistribution.query.filter(CmmProductGridDistribution.id_grid==id)
        return [{
            "size": m.size,
            "color": m.color,
            "value": m.value,
            "is_percent": m.is_percent
        } for m in rquery.items]

    @ns_prodg.response(HTTPStatus.OK.value,"Cria uma nova grade no sistema")
    @ns_prodg.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova grade!")
    @ns_prodg.doc(parser=grid_model)
    def post(self)->int:
        try:
            req = request.get_json("product_grid")
            grid = CmmProductGrid()
            grid.name = req.name
            db.session.add(grid)
            db.session.commit()
            for dist in req.distribution:
                gridd = CmmProductGridDistribution()
                gridd.id_grid    = grid.id
                gridd.color      = dist.color
                gridd.size       = dist.size
                gridd.value      = dist.value
                gridd.is_percent = dist.is_percent
                db.session.add(gridd)
                db.session.commit()
            return grid.id
        except:
            return 0


@ns_prodg.route("/<int:id>")
class Grid(Resource):
    @ns_prodg.response(HTTPStatus.OK.value,"Obtem um registro de uma grade",grid_model)
    @ns_prodg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def get(self,id:int):
        grid = CmmProductGrid.query.get(id)
        return {
            "id": grid.id,
            "name": grid.name,
            "distribution": self.get_distribution(grid.id)
        }
    
    def get_distribution(self,id:int):
        rquery = CmmProductGridDistribution.query.filter(CmmProductGridDistribution.id_grid==id)
        return [{
            "size": m.size,
            "color": m.color,
            "value": m.value,
            "is_percent": m.is_percent
        } for m in rquery.items]

    @ns_prodg.response(HTTPStatus.OK.value,"Salva dados de uma grade")
    @ns_prodg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def post(self,id:int)->bool:
        try:
            req = request.get_json("product_grid")

            grid = CmmProductGrid.query.get(id)
            grid.name = grid.name if req.name==None else req.name
            db.session.add(grid)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_prodg.response(HTTPStatus.OK.value,"Exclui os dados de uma grade")
    @ns_prodg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def delete(self,id:int)->bool:
        try:
            grid = CmmProductGrid.query.get(id)
            grid.trash = True
            db.session.add(grid)
            db.session.commit()
            return True
        except:
            return False