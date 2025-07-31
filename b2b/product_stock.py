import simplejson
from auth import auth
from os import environ
from flask import request
from decimal import Decimal
from http import HTTPStatus
from datetime import datetime
from models.helpers import _get_params, db
from flask_restx import Resource,Namespace,fields
from sqlalchemy import Delete, Select, and_, exc, or_, desc, asc
from models.tenant import CmmTranslateColors, CmmTranslateSizes, ScmEvent
from models.tenant import B2bBrand, B2bCartShopping, B2bCollection, B2bProductStock
from models.tenant import B2bTablePrice, B2bTablePriceProduct, CmmCategories, CmmMeasureUnit
from models.tenant import CmmProducts, CmmProductsCategories, CmmProductsGrid, CmmProductsGridDistribution 
from models.tenant import CmmProductsGridSizes, CmmProductsImages, CmmProductsModels, CmmProductsTypes

ns_stock = Namespace("product-stock",description="Operações para manipular dados de estoques de produtos")

stock_pag_model = ns_stock.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

stock_model = ns_stock.model(
    "ProductStock",{
        "id_product": fields.Integer,
        "color": fields.String,
        "size": fields.String,
        "quantity": fields.Integer,
        "limited": fields.Boolean
    }
)

prd_img_model = ns_stock.model(
    "ProductImages",{
        "id_product": fields.Integer,
        "img_url": fields.String
    }
)

prd_model = ns_stock.model(
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

prd_return = ns_stock.model(
    "ProductReturn",{
        "pagination": fields.Nested(stock_pag_model),
        "data": fields.List(fields.Nested(prd_model))
    }
)

stock_return = ns_stock.model(
    "ProductStockReturn",{
        "pagination": fields.Nested(stock_pag_model),
        "data": fields.List(fields.Nested(stock_model))
    }
)

@ns_stock.route("/")
class ProductStockList(Resource):
    @ns_stock.response(HTTPStatus.OK,"Obtem a lista de estoques de produtos do B2B",stock_return)
    @ns_stock.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_stock.param("page","Número da página de registros","query",type=int,required=True)
    @ns_stock.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_stock.param("query","Texto para busca","query")
    @ns_stock.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_stock.param("order_by","Campo de ordenacao","query")
    @ns_stock.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num    = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size   = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query      = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params    = _get_params(str(query))
            # trash     = False if not hasattr(params,"trash") else True
            # order_by  = "id" if not hasattr(params,"order_by") else params.order_by
            # direction = asc if not hasattr(params,"order") else asc if str(params.order).lower()=="asc" else desc
            search    = None if not hasattr(params,"search") else params.search if params is not None else None
            list_all  = False if not hasattr(params,"list_all") else True

            filter_brand    = None if not hasattr(params,"brand") else params.brand if params is not None else None
            filter_collect  = None if not hasattr(params,"collection") else params.collection if params is not None else None
            filter_category = None if not hasattr(params,"category") else params.category if params is not None else None
            filter_model    = None if not hasattr(params,"model") else params.model if params is not None else None
            filter_type     = None if not hasattr(params,"type") else params.type if params is not None else None
            filter_color    = None if not hasattr(params,"color") else params.color if params is not None else None

            pquery = Select(B2bProductStock.id_product,
                        CmmProductsGrid.id.label("id_grid"),
                        CmmProducts.refCode,
                        CmmProducts.name.label("product")
                        ).distinct()\
                .join(CmmProducts,CmmProducts.id==B2bProductStock.id_product)\
                .join(CmmProductsGrid,CmmProductsGrid.id==CmmProducts.id_grid)\
                .join(CmmTranslateColors,CmmTranslateColors.id==B2bProductStock.id_color)\
                .join(CmmTranslateSizes,CmmTranslateSizes.id==B2bProductStock.id_size)
            
            if filter_brand is not None:
                pquery = pquery.where(CmmProducts.id_collection.in_(
                    Select(B2bCollection.id)
                    .join(B2bBrand,B2bBrand.id==B2bCollection.id_brand)
                    .where(B2bBrand.id.in_(str(filter_brand).split(',')))
                ))

            if filter_collect is not None:
                pquery = pquery.where(CmmProducts.id_collection.in_(str(filter_collect).split(',')))

            if filter_category is not None:
                pquery = pquery.where(
                    CmmProducts.id.in_(
                        Select(CmmProductsCategories.id_product)
                        .where(CmmProductsCategories.id_category.in_(str(filter_category).split(',')))
                    )
                )

            if filter_model is not None:
                pquery = pquery.where(
                    CmmProducts.id_model.in_(str(filter_model).split(','))
                )

            if filter_type is not None:
                pquery = pquery.where(
                    CmmProducts.id_type.in_(str(filter_type).split(','))
                )

            if filter_color is not None:
                pquery = pquery.where(
                    CmmTranslateColors.id.in_(str(filter_color).split(','))
                )
            
            # color query
            cquery = Select(B2bProductStock.id_color,
                            CmmTranslateColors.name).distinct()\
                .join(CmmTranslateColors,CmmTranslateColors.id==B2bProductStock.id_color)
            
            # size query
            squery = Select(B2bProductStock.id_size,
                            CmmTranslateSizes.new_size.label("name"),
                            B2bProductStock.quantity,
                            B2bProductStock.ilimited,
                            B2bProductStock.in_order)\
                .join(CmmTranslateSizes,CmmTranslateSizes.id==B2bProductStock.id_size)
            
            # _show_query(pquery)

            if search is not None:
                pquery = pquery.where(
                    or_(
                        CmmProducts.name.like("%{}%".format(search)),
                        CmmProducts.refCode.like("%{}%".format(search)),
                        CmmProducts.observation.like("%{}%".format(search)),
                        CmmProducts.description.like("%{}%".format(search)),
                        CmmProducts.barCode.like("%{}%".format(search)),
                        CmmTranslateSizes.name.like("%{}%".format(search)),
                        CmmTranslateColors.name.like("%{}%".format(search)),
                        CmmTranslateColors.hexcode.like("%{}%".format(search))
                    )
                )
            
            # _show_query(pquery)

            if not list_all:
                pag = db.paginate(pquery,page=pag_num,per_page=pag_size)
                pquery = pquery.limit(pag_size).offset((pag_num -1) * pag_size)

                retorno =  {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next
                    },
                    "data":[{
                        "id_product":m.id_product,
                        "id_grid": m.id_grid,
                        "refCode": m.refCode,
                        "product": m.product,
                        "colors": [{
                            "id": c.id_color,
                            "name": c.name,
                            "sizes":[{
                                "id": s.id_size,
                                "name": s.name,
                                "quantity": s.quantity,
                                "in_order": s.in_order,
                                "ilimited": s.ilimited 
                            }for s in db.session.execute(squery.where(and_(B2bProductStock.id_product==m.id_product,B2bProductStock.id_color==c.id_color)))]
                        }for c in db.session.execute(cquery.where(B2bProductStock.id_product==m.id_product))]
                    } for m in db.session.execute(pquery)]
                }
            else:
                retorno = [{
                        "id_product":m.id_product,
                        "id_grid": m.id_grid,
                        "refCode": m.refCode,
                        "product": m.product,
                        "colors": [{
                            "id": c.id_color,
                            "name": c.name,
                            "sizes":[{
                                "id": s.id_size,
                                "name": s.name,
                                "quantity": s.quantity,
                                "in_order": s.in_order,
                                "ilimited": s.ilimited 
                            }for s in db.session.execute(squery.where(and_(B2bProductStock.id_product==m.id_product,B2bProductStock.id_color==c.id_color)))]
                        }for c in db.session.execute(cquery.where(B2bProductStock.id_product==m.id_product))]
                    } for m in db.session.execute(pquery)]
                
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_stock.response(HTTPStatus.OK,"Cria um registro de estoque de produto do B2B")
    @ns_stock.response(HTTPStatus.BAD_REQUEST,"Falha ao criar nova condicao de pagamento!")
    @ns_stock.param("name","Nome da condição de pagamento","formData",required=True)
    @ns_stock.param("received_days","Dias para recebimento","formData",type=int,required=True)
    @ns_stock.param("installments","Número de parcelas","formData",type=int,required=True)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()

            stock = B2bProductStock()
            stock.id_product = req["id_product"]
            stock.id_color   = req["id_color"]
            stock.id_size    = req["id_size"]
            stock.quantity   = req["quantity"]
            stock.ilimited   = req["ilimited"]
            db.session.add(stock)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    def patch(self):
        try:
            req = request.get_json()
            # varre cada um dos produtos
            for id_product in req["ids"]:
                for id_color in req["colors"]:
                    for size in req["grid"]:
                        stk = B2bProductStock.query.get((id_product,id_color,size["id"]))
                        if stk is not None:
                            stk.quantity = None if req["ilimited"] or req["ilimited"]=="true" else size["value"]
                            stk.ilimited = True if req["ilimited"] or req["ilimited"]=="true" else False
                            db.session.commit()
                        else:
                            stk = B2bProductStock()
                            stk.id_product = id_product
                            stk.id_color   = id_color
                            stk.id_size    = size["id"]
                            setattr(stk,"quantity",(None if req["ilimited"] or req["ilimited"]=="true" else size["value"]))
                            setattr(stk,"ilimited",(True if req["ilimited"] or req["ilimited"]=="true" else False))
                            db.session.add(stk)
                            db.session.commit()

                        if req["remove"] or req["remove"]=="true":
                            db.session.execute(Delete(B2bProductStock).where(
                                and_(
                                    B2bProductStock.id_product==id_product,
                                    B2bProductStock.id_color==id_color,
                                    B2bProductStock.id_size==size["id"]
                                )
                            ))
                            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_stock.route("/<int:id>")
@ns_stock.param("id","Id do produto")
@ns_stock.param("color","Cor do produto")
@ns_stock.param("size","Tamanho do produto")
class ProductStockApi(Resource):
    @ns_stock.response(HTTPStatus.OK,"Obtem um registro do estoque de um produto do B2B",stock_model)
    @ns_stock.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int,color:str,size:str):
        try:
            reg:B2bProductStock|None  = B2bProductStock.query.get([id,color,size])
            if reg is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST
            
            return {
                "id_product": reg.id_product,
                "id_color": reg.id_color,
                "id_size": reg.id_size,
                "quantity": reg.quantity,
                "in_order": reg.in_order,
                "ilimited": reg.ilimited
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_stock.response(HTTPStatus.OK,"Salva dados de um estoque")
    @ns_stock.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int,color:str,size:str):
        try:
            req = request.get_json()
            stock:B2bProductStock| None = B2bProductStock.query.get([id,color,size])
            if stock is not None:
                stock.id_product  = req["id_product"]
                stock.id_color    = req["id_color"]
                stock.id_size     = req["id_size"]
                stock.in_order    = req["in_order"]
                stock.quantity    = req["quantity"]
                stock.ilimited    = req["ilimited"]
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_stock.response(HTTPStatus.OK,"Exclui os dados de uma condição de pagamento")
    @ns_stock.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int,color:str,size:str):
        try:
            payCond = B2bProductStock.query.get([id,color,size])
            setattr(payCond,"trash",True)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

class ProductStockLoad(Resource):
    @ns_stock.response(HTTPStatus.OK,"Obtem a lista de estoques de um determinado produto do B2B")
    @ns_stock.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @auth.login_required
    def get(self,id_product:int):    
        cquery = Select(CmmTranslateColors.hexcode,CmmTranslateColors.name,CmmTranslateColors.color,CmmTranslateColors.id)\
            .distinct(B2bProductStock.id_color).select_from(B2bProductStock)\
            .join(CmmTranslateColors,CmmTranslateColors.id==B2bProductStock.id_color)\
            .filter(B2bProductStock.id_product==id_product)\
            .order_by(asc(B2bProductStock.id_color))

        cquery = db.session.execute(cquery)
        
        return [{
            "color_id"  : m.id,
            "color_name": m.name,
            "color_hexa": m.hexcode,
            "color_code": m.color,
            "sizes": self.get_sizes(id_product,m.id)
        }for m in cquery]
    
    def get_sizes(self,id_product:int,color:int):
        # subquery = Select(B2bProductStock.quantity,B2bProductStock.ilimited,B2bProductStock.id_size.label("size_code"))\
        #     .where(and_(B2bProductStock.id_product==id_product,B2bProductStock.id_color==color))\
        #     .cte()
        
        query = Select(
                CmmTranslateSizes.new_size.label("size_code"),
                CmmTranslateSizes.id,
                CmmTranslateSizes.name,
                B2bProductStock.quantity,
                B2bProductStock.ilimited,
                B2bCartShopping.quantity.label("value"))\
            .join(CmmProducts,CmmProducts.id==B2bProductStock.id_product)\
            .join(CmmProductsGrid,CmmProductsGrid.id==CmmProducts.id_grid)\
            .join(CmmProductsGridSizes,CmmProductsGridSizes.id_grid==CmmProductsGrid.id)\
            .join(CmmTranslateSizes,CmmTranslateSizes.id==CmmProductsGridSizes.id_size)\
            .outerjoin(B2bCartShopping,
                       and_(
                           B2bCartShopping.id_product==CmmProducts.id,
                           B2bCartShopping.id_color==color,
                           B2bCartShopping.id_size==B2bProductStock.id_size
                       ))\
            .where(and_(
                B2bProductStock.id_product==id_product,
                B2bProductStock.id_color==color,
                CmmProductsGridSizes.id_size==B2bProductStock.id_size
            ))
        
        # _show_query(query)

        query = db.session.execute(query)

        return [{
                "size_id": s.id,
                "size_code": s.size_code,
                "size_name": s.name,
                "size_value": self.formatQuantity(s.quantity,s.ilimited),
                "size_saved": 0 if s.value is None else s.value
            }for s in query]
    
    def formatQuantity(self,quantity:int,ilimited:bool):
        if (quantity is None or quantity == 0) and ilimited is True:
            return "999+"
        if (quantity is None or quantity == 0) and ilimited is None:
            return None
        return quantity

ns_stock.add_resource(ProductStockLoad,"/load-by-product/<int:id_product>")

#busca especifica para a galeria de produtos do B2B, jah que precisa buscar mais coisas além do nome
#so irah buscar produtos que tiverem estoque disponivel para o B2B
class ProductsGallery(Resource):
    @ns_stock.response(HTTPStatus.OK,"Obtem a listagem de produto",prd_return)
    @ns_stock.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_stock.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_stock.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_stock.param("query","Texto com parametros para busca","query")
    @auth.login_required
    def get(self):
        pag_num    = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size   = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query      = "" if request.args.get("query") is None or request.args.get("query")=="" else request.args.get("query")

        try:
            params     =  _get_params(str(query))
            order_by   = "id" if not hasattr(params,"order_by") else params.order_by if params is not None else 'id'
            direction  = asc if not hasattr(params,'order') else asc if params is not None and params.order=='ASC' else desc
            list_all   = False if not hasattr(params,"list_all") else True
            search     = None if not hasattr(params,"search") else params.search if params is not None else None

            filter_brand      = None if not hasattr(params,"brand") else params.brand if params is not None else None
            filter_collection = None if not hasattr(params,"collection") else params.collection if params is not None else None
            filter_category   = None if not hasattr(params,"category") else params.category if params is not None else None
            filter_model      = None if not hasattr(params,"model") else params.model if params is not None else None
            filter_type       = None if not hasattr(params,"type") else params.type if params is not None else None
            filter_color      = None if not hasattr(params,"color") else params.color if params is not None else None
            filter_size       = None if not hasattr(params,"size")else params.size if params is not None else None

            str_today = datetime.now().isoformat()[0:10]
            today = datetime.strptime(str_today,"%Y-%m-%d")

            #realiza a busca das colecoes que tem restricao no calendario
            rquery = Select(CmmProducts.id,CmmProducts.id_grid,CmmProducts.prodCode,CmmProducts.barCode,
                            CmmProducts.refCode,CmmProducts.name,CmmProducts.description,CmmProducts.observation,
                            CmmProducts.ncm,CmmProducts.price,CmmProducts.price_pos,CmmMeasureUnit.code.label("measure_unit"),CmmProducts.structure,
                            CmmProducts.date_created,CmmProducts.date_updated,CmmCategories.name.label("category_name"),
                            B2bCollection.name.label("collection_name"),B2bBrand.name.label("brand_name"),
                            CmmProductsTypes.name.label("product_type_name"),CmmProductsModels.name.label("product_model_name"))\
                .join(CmmProductsTypes,CmmProductsTypes.id==CmmProducts.id_type)\
                .join(CmmProductsModels,CmmProductsModels.id==CmmProducts.id_model)\
                .join(CmmMeasureUnit,CmmMeasureUnit.id==CmmProducts.id_measure_unit)\
                .outerjoin(B2bCollection,B2bCollection.id==CmmProducts.id_collection)\
                .outerjoin(B2bBrand,B2bBrand.id==B2bCollection.id_brand)\
                .outerjoin(B2bTablePriceProduct,B2bTablePriceProduct.id_product==CmmProducts.id)\
                .outerjoin(B2bTablePrice,B2bTablePrice.id==B2bTablePriceProduct.id_table_price)\
                .outerjoin(CmmProductsCategories,CmmProductsCategories.id_product==CmmProducts.id)\
                .outerjoin(CmmCategories,CmmCategories.id==CmmProductsCategories.id_category)\
                .where(CmmProducts.trash.is_(False))\
                .where(CmmProducts.id.in_(
                    Select(B2bProductStock.id_product).where(
                        or_(
                            B2bProductStock.quantity > 0, #possui quantidade indiferente de tamanho e cor
                            and_( #produto ilimitado
                                or_(
                                    B2bProductStock.quantity.__eq__(0),
                                    B2bProductStock.quantity.is_(None)
                                ),
                                B2bProductStock.ilimited.is_(True)
                            )
                        )
                    ))
                ).where(
                    B2bCollection.id.in_(
                        Select(ScmEvent.id_collection).where(
                            and_( #esta dentro do periodo
                                ScmEvent.year.__eq__(datetime.now().year),
                                ScmEvent.start_date.__gt__(today),
                                ScmEvent.end_date.__lt__(today)
                            )
                        )
                    )
                )
            
            #busca as colecoes que nao possuem restricao (irrestrict)
            iquery = Select(CmmProducts.id,CmmProducts.id_grid,CmmProducts.prodCode,CmmProducts.barCode,
                            CmmProducts.refCode,CmmProducts.name,CmmProducts.description,CmmProducts.observation,
                            CmmProducts.ncm,CmmProducts.price,CmmProducts.price_pos,CmmMeasureUnit.code.label("measure_unit"),CmmProducts.structure,
                            CmmProducts.date_created,CmmProducts.date_updated,CmmCategories.name.label("category_name"),
                            B2bCollection.name.label("collection_name"),B2bBrand.name.label("brand_name"),
                            CmmProductsTypes.name.label("product_type_name"),CmmProductsModels.name.label("product_model_name"))\
                .join(CmmProductsTypes,CmmProductsTypes.id==CmmProducts.id_type)\
                .join(CmmProductsModels,CmmProductsModels.id==CmmProducts.id_model)\
                .join(CmmMeasureUnit,CmmMeasureUnit.id==CmmProducts.id_measure_unit)\
                .outerjoin(B2bCollection,B2bCollection.id==CmmProducts.id_collection)\
                .outerjoin(B2bBrand,B2bBrand.id==B2bCollection.id_brand)\
                .outerjoin(B2bTablePriceProduct,B2bTablePriceProduct.id_product==CmmProducts.id)\
                .outerjoin(B2bTablePrice,B2bTablePrice.id==B2bTablePriceProduct.id_table_price)\
                .outerjoin(CmmProductsCategories,CmmProductsCategories.id_product==CmmProducts.id)\
                .outerjoin(CmmCategories,CmmCategories.id==CmmProductsCategories.id_category)\
                .where(CmmProducts.trash.is_(False))\
                .where(CmmProducts.id.in_(
                    Select(B2bProductStock.id_product).where(
                        or_(
                            B2bProductStock.quantity > 0, #possui quantidade indiferente de tamanho e cor
                            and_( #produto ilimitado
                                or_(
                                    B2bProductStock.quantity.__eq__(0),
                                    B2bProductStock.quantity.is_(None)
                                ),
                                B2bProductStock.ilimited.is_(True)
                            )
                        )
                    ))
                ).where(
                    B2bCollection.id.not_in(
                        Select(ScmEvent.id_collection).where(
                            and_( #que nao esta dentro do periodo
                                ScmEvent.year.__eq__(datetime.now().year),
                                ScmEvent.start_date.__gt__(today),
                                ScmEvent.end_date.__lt__(today)
                            )
                        )
                    )
                )

            #color query
            cquery = Select(CmmTranslateColors.name,CmmTranslateColors.id,CmmTranslateColors.hexcode)\
                .select_from(CmmTranslateColors).distinct()\
                .join(B2bProductStock,B2bProductStock.id_color==CmmTranslateColors.id)\
                .join(CmmProducts,CmmProducts.id==B2bProductStock.id_product)\
                .join(CmmProductsGrid,CmmProductsGrid.id==CmmProducts.id_grid)
                    # .join(CmmProductsGridDistribution,CmmProductsGridDistribution.id_color==CmmTranslateColors.id)\
                    # .join(CmmProductsGrid,CmmProductsGrid.id==CmmProductsGridDistribution.id_grid)\
                    # .join(B2bProductStock,B2bProductStock.id_color==CmmTranslateColors.id)
            
            # _show_query(cquery)
            
            if search is not None:
                rquery = rquery.where(and_(CmmProducts.trash.is_(False),or_(
                    CmmProducts.name.like(search),
                    CmmProducts.description.like(search),
                    CmmProducts.barCode.like(search),
                    CmmProducts.observation.like(search),
                    CmmCategories.name.like(search),
                    CmmProductsModels.name.like(search),
                    CmmProductsTypes.name.like(search)
                )))

                iquery = iquery.where(and_(CmmProducts.trash.is_(False),or_(
                    CmmProducts.name.like(search),
                    CmmProducts.description.like(search),
                    CmmProducts.barCode.like(search),
                    CmmProducts.observation.like(search),
                    CmmCategories.name.like(search),
                    CmmProductsModels.name.like(search),
                    CmmProductsTypes.name.like(search)
                )))
            if filter_brand is not None:      
                rquery = rquery.where(B2bBrand.id.in_(filter_brand.split(',')))
                iquery = iquery.where(B2bBrand.id.in_(filter_brand.split(',')))
            if filter_collection is not None: 
                rquery = rquery.where(B2bCollection.id.in_(filter_collection.split(",")))
                iquery = iquery.where(B2bCollection.id.in_(filter_collection.split(",")))
            if filter_category is not None:   
                rquery = rquery.where(CmmProducts.id.in_(
                    Select(CmmProductsCategories.id_product).where(CmmProductsCategories.id_category.in_(filter_category.split(",")))
                ))
                iquery = iquery.where(CmmProducts.id.in_(
                    Select(CmmProductsCategories.id_product).where(CmmProductsCategories.id_category.in_(filter_category.split(",")))
                ))
            if filter_model is not None:
                rquery = rquery.where(CmmProductsModels.id.in_(filter_model.split(",")))
                iquery = iquery.where(CmmProductsModels.id.in_(filter_model.split(",")))
            if filter_type is not None:
                rquery = rquery.where(CmmProductsTypes.id.in_(filter_type.split(",")))
                iquery = iquery.where(CmmProductsTypes.id.in_(filter_type.split(",")))
            if filter_color is not None:
                rquery = rquery.where(CmmProducts.id.in_(
                    Select(B2bProductStock.id_product).where(
                        B2bProductStock.id_color.in_(filter_color.split(","))
                    ))
                )
                
                iquery = iquery.where(CmmProducts.id.in_(
                    Select(B2bProductStock.id_product).where(
                        B2bProductStock.id_color.in_(filter_color.split(","))
                    ))
                )
                # rquery = rquery.where(CmmProducts.id_grid.in_(
                #     Select(CmmProductsGridDistribution.id_grid)\
                #     .join(B2bProductStock,and_(B2bProductStock.id_color==CmmProductsGridDistribution.id_color,B2bProductStock.id_size==CmmProductsGridDistribution.id_size))
                #     .where(and_(
                #         CmmProductsGridDistribution.id_color.in_(filter_color.split(",")),
                #         B2bProductStock.id_product==CmmProducts.id
                #     ))
                # ))
                # iquery = iquery.where(CmmProducts.id_grid.in_(
                #     Select(CmmProductsGridDistribution.id_grid)\
                #     .join(B2bProductStock,and_(B2bProductStock.id_color==CmmProductsGridDistribution.id_color,B2bProductStock.id_size==CmmProductsGridDistribution.id_size))
                #     .where(and_(
                #         CmmProductsGridDistribution.id_color.in_(filter_color.split(",")),
                #         B2bProductStock.id_product==CmmProducts.id
                #     ))
                # ))
            
            if filter_size is not None:
                rquery = rquery.where(CmmProducts.id_grid.in_(
                    Select(CmmProductsGridDistribution.id_size.in_(filter_size.split(",")))
                ))
                iquery = iquery.where(CmmProducts.id_grid.in_(
                    Select(CmmProductsGridDistribution.id_size.in_(filter_size.split(",")))
                ))

            rquery = rquery.union(iquery)

            # _show_query(rquery)

            if order_by=='price':
                rquery = rquery.order_by(direction(order_by))
            elif order_by=='category':
                rquery = rquery.order_by(direction("category_name"))
            elif order_by=='collection':
                rquery = rquery.order_by(direction("collection_name"))
            elif order_by=='brand':
                rquery = rquery.order_by(direction("brand_name"))
            elif order_by=='model':
                rquery = rquery.order_by(direction("product_model_name"))
            elif order_by=='type':
                rquery = rquery.order_by(direction("product_type_name"))
            elif order_by=='id':
                rquery = rquery.order_by(direction(order_by))

            if list_all is False:
                pag = db.paginate(rquery,page=pag_num,per_page=pag_size) # type: ignore
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
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None,
                        "images": self.get_images(m.id),
                        "colors": [{
                            "id": c.id,
                            "name": c.name,
                            "color": c.hexcode
                        }for c in db.session.execute(cquery.where(and_(CmmProductsGrid.id==m.id_grid,B2bProductStock.id_product==m.id)))]
                    } for m in db.session.execute(rquery)]
                }
            else:
                return [{
                        "id": m.id,
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
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None,
                        "images": self.get_images(m.id),
                        "colors": [{
                            "id": c.id,
                            "name": c.name,
                            "color": c.hexcode
                        }for c in db.session.execute(cquery.where(and_(CmmProductsGrid.id==m.id_grid,B2bProductStock.id_product==m.id)))]
                    } for m in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    def get_images(self,id:int):
        rquery = CmmProductsImages.query.filter_by(id_product=id)
        return [{
            "id": m.id,
            "img_url":m.img_url,
            "default":m.img_default
        }for m in rquery]
ns_stock.add_resource(ProductsGallery,'/gallery/')