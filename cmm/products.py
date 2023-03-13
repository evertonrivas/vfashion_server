from http import HTTPStatus
import json
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmProducts,CmmProductsSku,CmmProductsGrid,CmmProductsGridDistribution,db
import sqlalchemy as sa
from sqlalchemy import exc
from auth import auth

ns_prod  = Namespace("products",description="Operações para manipular dados de produtos")
ns_gprod = Namespace("products-grid",description="Operações para manipular dados das grades de produtos")


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
        "id_product": fields.Integer,
        "id_type": fields.Integer,
        "id_model": fields.Integer,
        "size": fields.String,
        "color": fields.String
    }
)

prd_model = ns_prod.model(
    "Product",{
        "id": fields.Integer,
        "id_category": fields.Integer,
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
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime,
        "sku": fields.List(fields.Nested(prd_sku_model))
    }
)

prd_return = ns_prod.model(
    "ProductReturn",{
        "pagination": fields.Nested(prd_pag_model),
        "data": fields.List(fields.Nested(prd_model))
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
    @ns_prod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_prod.param("query","Texto para busca","query")
    #@auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
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
                    "id_category": m.id_category,
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
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None,
                    "sku": self.get_sku(m.id)
                } for m in rquery.items]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    def get_sku(self,id:int):
        rquery = CmmProductsSku.query.filter_by(id_product=id)
        return [{
            "id_type": m.id_type,
            "id_model": m.id_model,
            "color": m.color,
            "size" : m.size
        }for m in rquery.items]

    @ns_prod.response(HTTPStatus.OK.value,"Cria um novo produto no sistema")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo produto!")
    @ns_prod.doc(body=prd_model)
    #@auth.login_required
    def post(self)->int:
        try:
            req = json.dumps(request.get_json())
            prod = CmmProducts()
            prod.id_category   = int(req.id_category)
            prod.prodCode      = req.prodCode
            prod.barCode       = req.barCode
            prod.refCode       = req.refCode
            prod.name          = req.name
            prod.description   = req.description
            prod.observation   = req.observation
            prod.ncm           = req.ncm
            prod.image         = req.image
            prod.price         = float(req.price)
            prod.measure_unit  = req.measure_unit
            db.session.add(prod)
            db.session.commit()
            for s in req.sku:
                sku = CmmProductsSku()
                sku.id_product = prod.id
                sku.id_type    = s.id_type
                sku.id_model   = s.id_model
                sku.color      = s.color
                sku.size       = s.size
                db.session.add(sku)
                db.session.commit()
            
            return prod.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


@ns_prod.route("/<int:id>")
@ns_prod.param("id","Id do registro")
class ProductApi(Resource):

    @ns_prod.response(HTTPStatus.OK.value,"Obtem um registro de produto",prd_model)
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def get(self,id:int):
        try:
            rquery = CmmProducts.query.get(id)
            squery = CmmProductsSku.query.filter_by(id_product=id)
            return {
                "id": rquery.id,
                "prodCode": rquery.prodCode,
                "barCode": rquery.barCode,
                "refCode": rquery.refCode,
                "name": rquery.Name,
                "description": rquery.description,
                "observation": rquery.observation,
                "ncm": rquery.ncm,
                "image": rquery.image,
                "price": rquery.price,
                "measure_unit": rquery.measure_unit,
                "structure": rquery.structure,
                "date_created": rquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": rquery.date_updated.strftime("%Y-%m-%d %H:%M:%S") if rquery.date_updated!=None else None
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_prod.response(HTTPStatus.OK.value,"Salva dados de um produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def post(self,id:int)->bool:
        try:
            req = json.dumps(request.get_json())
            prod = CmmProducts.query.get(id)
            prod.id_category   = prod.id_category if req.id_category is None else int(req.id_category)
            prod.id_prod_type  = prod.id_prod_type if req.id_prod_type is None else int(req.id_prod_type)
            prod.id_prod_model = prod.id_prod_model if req.id_prod_model is None else int(req.id_prod_model)
            prod.prodCode      = prod.prodCode if req.prodCode is None else req.prodCode
            prod.barCode       = prod.barCode if req.barCode is None else req.barCode
            prod.refCode       = prod.refCode if req.refCode is None else req.refCode
            prod.name          = prod.name if req.name is None else req.name
            prod.description   = prod.description if req.description is None else req.description
            prod.observation   = prod.observation if req.observation is None else req.observation
            prod.ncm           = prod.ncm if req.ncm is None else req.ncm
            prod.image         = prod.image if req.image is None else req.image
            prod.price         = prod.price if req.price is None else float(req.price)
            prod.measure_unit  = prod.measure_unit if req.measure_unit is None else req.measure_unit
            prod.trash         = prod.trash if req.trash is None else req.trash
            db.session.commit()

            #apaga todos os SKUs registrados e realiza novo registro
            #eh mais facil do que realizar testes para saber se saiu ou entrou registro
            db.session.delete(CmmProductsSku()).where(CmmProductsSku().id_product==id)
            db.session.commit()
            for s in req.sku:
                sku = CmmProductsSku()
                sku.id_product = id
                sku.id_type    = s.id_type
                sku.id_model   = s.id_model
                sku.color      = s.color
                sku.size       = s.size
                db.session.add(sku)
                db.session.commit()


            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_prod.response(HTTPStatus.OK.value,"Exclui os dados de um produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def delete(self,id:int)->bool:
        try:
            prod = CmmProducts.query.get(id)
            prod.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

####################################################################################
#           INICIO DAS CLASSES QUE IRAO TRATAR AS GRADES DE  PRODUTOS.             #
####################################################################################

grd_pag_model = ns_gprod.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

grd_dist_model = ns_gprod.model(
    "Distribution",{
        "size": fields.String,
        "color": fields.String,
        "value": fields.Integer,
        "is_percent": fields.Boolean
    }
)

grd_model = ns_gprod.model(
    "Grid",{
        "id": fields.Integer,
        "name": fields.String,
        "distribution": fields.List(fields.Nested(grd_dist_model))
    }
)

grd_return = ns_gprod.model(
    "GridReturn",{
        "pagination": fields.Nested(grd_pag_model),
        "data": fields.List(fields.Nested(grd_model))
    }
)


@ns_gprod.route("/")
class GridList(Resource):

    @ns_gprod.response(HTTPStatus.OK.value,"Obtem os registros de grades existentes",grd_return)
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_gprod.param("page","Número da página de registros","query",type=int,required=True)
    @ns_gprod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_gprod.param("query","Texto para busca","query")
    #@auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
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
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
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
    @ns_gprod.doc(body=grd_model)
    #@auth.login_required
    def post(self)->int:
        try:
            req = json.dumps(request.get_json())
            grid = CmmProductsGrid()
            grid.name = req.name
            db.session.add(grid)
            db.session.commit()

            for dist in req.distribution:
                gridd         = CmmProductsGridDistribution()
                gridd.id_grid = grid.id
                gridd.color   = dist.color
                gridd.size    = dist.size
                gridd.value   = dist.value
                gridd.is_percent = dist.is_percent
                db.session.add(gridd)
                db.session.commit()

            return grid.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


@ns_gprod.route("/<int:id>")
@ns_prod.param("id","Id do registro")
class GridApi(Resource):
    @ns_gprod.response(HTTPStatus.OK.value,"Obtem um registro de uma grade",grd_model)
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def get(self,id:int):
        try:
            grid = CmmProductsGrid.query.get(id)
            dist = CmmProductsGridDistribution.query.find_by(id_grid=id)
            return {
                "id": id,
                "name": grid.name,
                "distribution":[{
                    "size": m.size,
                    "color": m.color,
                    "value": m.value,
                    "is_percent": m.is_percent
                } for m in dist.items]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_gprod.response(HTTPStatus.OK.value,"Salva dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def post(self,id:int)->bool:
        try:
            req = json.dumps(request.get_json())
            grid = CmmProductsGrid.query.get(id)
            grid.name = grid.name if req.name is None else req.name
            grid.trash = grid.trash if req.trash is None else req.trash
            db.session.commit()

            #apaga e recria as distribuicoes
            db.session.delete(CmmProductsGridDistribution()).where(CmmProductsGridDistribution().id_grid==id)
            db.session.commit()
            for dist in grid.distribution:
                gridd         = CmmProductsGridDistribution()
                gridd.id_grid = id
                gridd.color   = dist.color
                gridd.size    = dist.size
                gridd.value   = dist.value
                gridd.is_percent = dist.is_percent
                db.session.add(gridd)
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_gprod.response(HTTPStatus.OK.value,"Exclui os dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def delete(self,id:int)->bool:
        try:
            grid       = CmmProductsGrid.query.get(id)
            grid.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }