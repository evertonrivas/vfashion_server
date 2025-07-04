from http import HTTPStatus
import simplejson
from flask_restx import Resource,Namespace,fields
from flask import request
from f2bconfig import ProductMassiveAction
from models import B2bCollection, B2bProductStock, CmmCategories, CmmMeasureUnit, CmmProducts, CmmProductsCategories
from models import CmmProductsGrid, CmmProductsImages, CmmProductsTypes, CmmProductsModels
from models import _get_params, db
# from models import _show_query
from sqlalchemy import Delete, Update, desc, exc, asc,Select, or_
from auth import auth
from decimal import Decimal
from os import environ

ns_prod  = Namespace("products",description="Operações para manipular dados de produtos")


prd_pag_model = ns_prod.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

prd_img_model = ns_prod.model(
    "ProductImages",{
        "id_product": fields.Integer,
        "img_url": fields.String
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
        "price": fields.Float,
        "measure_unit": fields.String,
        "structure": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime,
        "images": fields.List(fields.Nested(prd_img_model))
    }
)

prd_return = ns_prod.model(
    "ProductReturn",{
        "pagination": fields.Nested(prd_pag_model),
        "data": fields.List(fields.Nested(prd_model))
    }
)

####################################################################################
#                INICIO DAS CLASSES QUE IRA TRATAR OS PRODUTOS.                    #
####################################################################################
@ns_prod.route("/")
class ProductsList(Resource):
    @ns_prod.response(HTTPStatus.OK.value,"Obtem a listagem de produto",prd_return)
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_prod.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_prod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_prod.param("query","Texto para busca","query")
    @ns_prod.param("order_by","Campo de ordenacao","query")
    @ns_prod.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query   = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params = _get_params(query)
            trash     = False if hasattr(params,"trash")==False else True
            order_by  = "name" if hasattr(params,"order_by")==False else params.order_by
            direction = asc if hasattr(params,"order")==False else asc if str(params.order).lower()=="asc" else desc
        
            filter_search     = None if hasattr(params,"search")==False else params.name
            filter_brand      = None if hasattr(params,"brand")==False else params.brand
            filter_collection = None if hasattr(params,"collection")==False else params.collection
            filter_category   = None if hasattr(params,"category")==False else params.category
            filter_type       = None if hasattr(params,"type")==False else params.type
            filter_model      = None if hasattr(params,"model")==False else params.model
            filter_grid       = None if hasattr(params,"grid")==False else params.grid
            filter_no_stock   = None if hasattr(params,"no_stock")==False else True

            rquery = Select(CmmProducts.id,
                            CmmProducts.prodCode,
                            CmmProducts.barCode,
                            CmmProducts.refCode,
                            CmmProducts.name,
                            CmmProducts.description,
                            CmmProducts.observation,
                            CmmProducts.ncm,
                            CmmProducts.price,
                            CmmProducts.price_pos,
                            CmmMeasureUnit.code.label("measure_unit"),
                            CmmProducts.structure,
                            CmmProducts.date_created,
                            CmmProducts.date_updated,
                            CmmProductsTypes.name.label("type_description"),
                            CmmProductsModels.name.label("model_description"),
                            CmmProductsGrid.name.label("grid_description")
                            ).outerjoin(CmmProductsTypes,CmmProductsTypes.id==CmmProducts.id_type)\
                            .outerjoin(CmmProductsModels,CmmProductsModels.id==CmmProducts.id_model)\
                            .outerjoin(CmmProductsGrid,CmmProductsGrid.id==CmmProducts.id_grid)\
                            .outerjoin(CmmMeasureUnit,CmmMeasureUnit.id==CmmProducts.id_measure_unit)\
                            .where(CmmProducts.trash==trash)\
                            .order_by(direction(getattr(CmmProducts, order_by)))
            
            cat_query = Select(CmmCategories.name).join(CmmProductsCategories,CmmProductsCategories.id_category==CmmCategories.id)

            # _show_query(rquery)
            
            if filter_search is not None:
                rquery = rquery.where(or_(
                    CmmProducts.name.like("%{}%".format(filter_search)),
                    CmmProducts.description.like("%{}%".format(filter_search)),
                    CmmProducts.observation.like("%{}%".format(filter_search)),
                    CmmProducts.barCode.like("%{}%".format(filter_search)),
                    CmmProducts.refCode.like("%{}%".format(filter_search))
                ))

            if filter_model is not None:
                rquery = rquery.where(CmmProducts.id_model==filter_model)

            if filter_type is not None:
                rquery = rquery.where(CmmProducts.id_type==filter_type)

            if filter_grid is not None:
                rquery = rquery.where(CmmProducts.id_grid==filter_grid)

            if filter_brand is not None:
                rquery = rquery.where(CmmProducts.id_collection.in_(
                    Select(B2bCollection.id).where(B2bCollection.id_brand.in_(
                        str(filter_brand).split(",")
                    ))
                ))
            
            if filter_collection is not None:
                rquery = rquery.where(CmmProducts.id_collection.in_(
                    str(filter_collection).split(",")
                ))

            if filter_category is not None:
                rquery = rquery.where(CmmProducts.id.in_(
                    Select(CmmProductsCategories.id_product)
                    .where(CmmProductsCategories.id_category.in_(
                        str(filter_category).split(",")
                    ))
                ))

            if filter_no_stock is True:
                rquery = rquery.where(CmmProducts.id.not_in(
                    Select(B2bProductStock.id_product.distinct())
                ))

            if hasattr(params,'list_all')==False:
                pag = db.paginate(rquery,page=pag_num,per_page=pag_size)
                rquery = rquery.limit(pag_size).offset((pag_num - 1) * pag_size)

                return {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next
                    },
                    "data":[{
                        "id": m.id,
                        "type_description": m.type_description,
                        "model_description": m.model_description,
                        "grid_description":m.grid_description,
                        "prodCode": m.prodCode,
                        "barCode": m.barCode,
                        "refCode": m.refCode,
                        "name": m.name,
                        "description": m.description,
                        "observation": m.observation,
                        "ncm": m.ncm,
                        "price": simplejson.dumps(Decimal(m.price)),
                        "price_pos": None if m.price_pos is None else simplejson.dumps(Decimal(m.price_pos)),
                        "measure_unit": m.measure_unit,
                        "structure": m.structure,
                        "categories": [{"name": c.name } for c in db.session.execute(cat_query.where(CmmProductsCategories.id_product==m.id))],
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                return [{
                        "id": m.id,
                        "type_description": m.type_description,
                        "model_description": m.model_description,
                        "grid_description":m.grid_description,
                        "prodCode": m.prodCode,
                        "barCode": m.barCode,
                        "refCode": m.refCode,
                        "name": m.name,
                        "description": m.description,
                        "observation": m.observation,
                        "ncm": m.ncm,
                        "price": simplejson.dumps(Decimal(m.price)),
                        "price_pos": None if m.price_pos is None else simplejson.dumps(Decimal(m.price_pos)),
                        "measure_unit": m.measure_unit,
                        "structure": m.structure,
                        "categories": [{"name": c.name } for c in db.session.execute(cat_query.where(CmmProductsCategories.id_product==m.id))],
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_prod.response(HTTPStatus.OK.value,"Cria um novo produto no sistema")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo produto!")
    @ns_prod.doc(body=prd_model)
    @auth.login_required
    def post(self)->int|dict:
        try:
            req = request.get_json()
            prod:CmmProducts = CmmProducts()
            prod.id_type       = req["id_type"]
            prod.id_model      = req["id_model"]
            prod.id_grid       = req["id_grid"]
            prod.prodCode      = req["prod_code"]
            prod.barCode       = req["bar_code"]
            prod.refCode       = req["ref_code"]
            prod.name          = req["name"]
            prod.description   = req["description"]
            prod.observation   = None if req["observation"]=="undefined" else req["observation"]
            prod.price         = float(req["price"])
            prod.price_pos     = None if req["price_pos"]=="null" or req["price_pos"] is None else float(req["price_pos"])
            prod.id_measure_unit = req["id_measure_unit"]
            db.session.add(prod)
            db.session.commit()

            if "images" in req:
                for image in req["images"]:
                    # significa que so irah atualizar as imagens
                    if image["id"] > 0:
                        if image["url"]!="":
                            img = CmmProductsImages.query.get(image["id"])
                            img.img_url = image["url"]
                            img.img_default = image["default"]
                            db.session.commit()
                    else:
                        if image["url"]!="":
                            img = CmmProductsImages()
                            img.id_product  = prod.id
                            img.img_url     = image["url"]
                            img.img_default = image["default"]
                            db.session.add(img)
                            db.session.commit()

            if "id_category" in req:
                if req["id_category"] is not None:
                    cat = CmmProductsCategories()
                    cat.id_category = req["id_category"]
                    cat.id_product  = prod.id
            
            return prod.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_prod.response(HTTPStatus.OK.value,"Exclui os dados de produto(s)")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def delete(self)->bool|dict:
        try:
            req = request.get_json()
            for id in req["ids"]:
                prod = CmmProducts.query.get(id)
                prod.trash = req["toTrash"]
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_prod.response(HTTPStatus.OK.value,"Realiza ações massivas em produto(s)")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def patch(self)->bool|dict:
        try:
            req = request.get_json()
            print(ProductMassiveAction.TYPE.value)
            if req["action"]==ProductMassiveAction.CATEGORY.value:
                db.session.execute(Delete(CmmProductsCategories).where(CmmProductsCategories.id_product.in_(req["products"])))
                db.session.commit()
                for id in req["ids"]:
                    for prod in req["products"]:
                        prod_cat = CmmProductsCategories()
                        prod_cat.id_product  = prod
                        prod_cat.id_category = id
                        db.session.add(prod_cat)
            elif req["action"]==ProductMassiveAction.GRID.value:
                db.session.execute(Update(CmmProducts).values(id_grid=req["ids"]).where(CmmProducts.id.in_(req["products"])))
            elif req["action"]==ProductMassiveAction.MODEL.value:
                db.session.execute(Update(CmmProducts).values(id_model=req["ids"]).where(CmmProducts.id.in_(req["products"])))
            elif req["action"]==ProductMassiveAction.PRICE.value:
                db.session.execute(Update(CmmProducts).values(price=req["ids"]).where(CmmProducts.id.in_(req["products"])))
            elif req["action"]==ProductMassiveAction.TYPE.value:
                db.session.execute(Update(CmmProducts).values(id_type=req["ids"]).where(CmmProducts.id.in_(req["products"])))
            else: #measure
                db.session.execute(Update(CmmProducts).values(id_measure_unit=req["ids"]).where(CmmProducts.id.in_(req["products"])))
            
            db.session.commit()

            return True
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
    @auth.login_required
    def get(self,id:int):
        try:
            rquery = CmmProducts.query.get(id)
            iquery = CmmProductsImages.query.filter_by(id_product=id)
            return {
                "id": rquery.id,
                "id_type": rquery.id_type,
                "id_model": rquery.id_model,
                "id_grid": rquery.id_grid,
                "prodCode": rquery.prodCode,
                "barCode": rquery.barCode,
                "refCode": rquery.refCode,
                "name": rquery.name,
                "description": rquery.description,
                "observation": rquery.observation,
                "ncm": rquery.ncm,
                "price": simplejson.dumps(Decimal(rquery.price)),
                "price_pos": None if rquery.price_pos is None else simplejson.dumps(Decimal(rquery.price_pos)),
                "id_measure_unit": rquery.id_measure_unit,
                "structure": rquery.structure,
                "date_created": rquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": rquery.date_updated.strftime("%Y-%m-%d %H:%M:%S") if rquery.date_updated!=None else None,
                "images":[{
                    "id": m.id,
                    "img_url": m.img_url,
                    "default": m.img_default
                }for m in iquery]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_prod.response(HTTPStatus.OK.value,"Salva dados de um produto")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def post(self,id:int)->bool|dict:
        try:
            req = request.get_json()
            prod:CmmProducts = CmmProducts.query.get(id)
            prod.id_type         = req["id_type"]
            prod.id_model        = req["id_model"]
            prod.id_grid         = req["id_grid"]
            prod.prodCode        = req["prod_code"]
            prod.barCode         = req["bar_code"]
            prod.refCode         = req["ref_code"]
            prod.name            = req["name"]
            prod.description     = req["description"]
            prod.observation     = None if req["observation"]=="undefined" else req["observation"]
            prod.price           = float(req["price"])
            prod.price_pos       = None if req["price_pos"]=="null" or req["price_pos"] is None else float(req["price_pos"])
            prod.id_measure_unit = req["id_measure_unit"]
            db.session.commit()

            if "images" in req:
                for image in req["images"]:
                    # significa que so irah atualizar as imagens
                    if image["id"] > 0:
                        if image["url"]!="":
                            img = CmmProductsImages.query.get(image["id"])
                            img.img_url = image["url"]
                            img.img_default = image["default"]
                            db.session.commit()
                    else:
                        if image["url"]!="":
                            img = CmmProductsImages()
                            img.id_product  = id
                            img.img_url     = image["url"]
                            img.img_default = image["default"]
                            db.session.add(img)
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
    @auth.login_required
    def delete(self,id:int)->bool|dict:
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