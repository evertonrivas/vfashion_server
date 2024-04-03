from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
import simplejson
from models import B2bBrand, B2bCollection, B2bCollectionPrice, B2bProductStock, B2bTablePrice, B2bTablePriceProduct, CmmCategories, CmmMeasureUnit, CmmProducts, CmmProductsCategories, CmmProductsGrid, CmmProductsGridDistribution, CmmProductsImages, CmmProductsModels, CmmProductsTypes, CmmTranslateColors, CmmTranslateSizes, ScmEvent, _get_params, _show_query, db
from sqlalchemy import Select, and_, exc,or_,desc,asc
from auth import auth
from config import Config

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
    @ns_stock.response(HTTPStatus.OK.value,"Obtem a lista de estoques de produtos do B2B",stock_return)
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_stock.param("page","Número da página de registros","query",type=int,required=True)
    @ns_stock.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_stock.param("query","Texto para busca","query")
    @ns_stock.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_stock.param("order_by","Campo de ordenacao","query")
    @ns_stock.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num    =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size   = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search     = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        list_all   = False if request.args.get("list_all") is None else True
        order_by   = "id" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc

        try:
            if search=="":
                rquery = B2bProductStock\
                    .query\
                    .filter(or_(B2bProductStock.color.like(search),B2bProductStock.size.like(search)))\
                    .order_by(direction(getattr(B2bProductStock, order_by)))
            else:
                rquery = B2bProductStock\
                    .query\
                    .order_by(direction(getattr(B2bProductStock, order_by)))

            if list_all==False:
                rquery.paginate(page=pag_num,per_page=pag_size)

                retorno =  {
                    "pagination":{
                        "registers": rquery.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": rquery.pages,
                        "has_next": rquery.has_next
                    },
                    "data":[{
                        "id_product":m.id_product,
                        "color": m.color,
                        "size": m.size,
                        "quantity": m.quantity,
                        "limited": m.limited
                    } for m in rquery.items]
                }
            else:
                retorno = [{
                        "id_product":m.id_product,
                        "color": m.color,
                        "size": m.size,
                        "quantity": m.quantity,
                        "limited": m.limited
                    } for m in rquery]
                
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_stock.response(HTTPStatus.OK.value,"Cria um registro de estoque de produto do B2B")
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova condicao de pagamento!")
    @ns_stock.param("name","Nome da condição de pagamento","formData",required=True)
    @ns_stock.param("received_days","Dias para recebimento","formData",type=int,required=True)
    @ns_stock.param("installments","Número de parcelas","formData",type=int,required=True)
    @auth.login_required
    def post(self)->int:
        try:
            stock = B2bProductStock()
            stock.id_product = int(request.form.get("id_product"))
            stock.id_color      = request.form.get("id_color")
            stock.id_size       = request.form.get("id_size")
            stock.quantity   = int(request.form.get("quantity"))
            stock.ilimited    = bool(request.form.get("ilimited"))
            db.session.add(stock)
            db.session.commit()
            return stock.id
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
    @ns_stock.response(HTTPStatus.OK.value,"Obtem um registro do estoque de um produto do B2B",stock_model)
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int,color:str,size:str):
        try:
            return B2bProductStock.query.get([id,color,size]).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_stock.response(HTTPStatus.OK.value,"Salva dados de uma condição de pgamento")
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_stock.param("quantiy","Quantidade do estoque","formData",required=True)
    @ns_stock.param("limited","Se o produto é limitado","formData",type=bool,required=True)
    @auth.login_required
    def post(self,id:int,color:str,size:str)->bool:
        try:
            stock = B2bProductStock.query.get([id,color,size])
            stock.quantity = stock.quantity if request.form.get("quantity") is None else int(request.form.get("quantity"))
            stock.limited  = stock.limited if request.form.get("limited") is None else bool(request.form.get("limited"))
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_stock.response(HTTPStatus.OK.value,"Exclui os dados de uma condição de pagamento")
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int,color:str,size:str)->bool:
        try:
            payCond = B2bProductStock.query.get([id,color,size])
            payCond.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

class ProductStockLoad(Resource):
    @ns_stock.response(HTTPStatus.OK.value,"Obtem a lista de estoques de um determinado produto do B2B")
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
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
        subquery = Select(B2bProductStock.quantity,B2bProductStock.ilimited,B2bProductStock.id_size.label("size_code"))\
            .where(and_(B2bProductStock.id_product==id_product,B2bProductStock.id_color==color))\
            .cte()
        query = Select(CmmTranslateSizes.new_size.label("size_code"),CmmTranslateSizes.id,CmmTranslateSizes.name,subquery.c.quantity,subquery.c.ilimited)\
            .outerjoin(subquery,subquery.c.size_code==CmmTranslateSizes.id)
        
        #_show_query(query)

        query = db.session.execute(query)

        return [{
                "size_id": s.id,
                "size_code": s.size_code,
                "size_name": s.name,
                "size_value": self.formatQuantity(s.quantity,s.ilimited),
                "size_saved": 0
            }for s in query]
    
    def formatQuantity(self,quantity:int,ilimited:bool):
        if (quantity is None or quantity == 0) and ilimited==True:
            return 99999
        if (quantity is None or quantity == 0) and ilimited is None:
            return None
        return quantity

ns_stock.add_resource(ProductStockLoad,"/load-by-product/<int:id_product>")

#busca especifica para a galeria de produtos do B2B, jah que precisa buscar mais coisas além do nome
#so irah buscar produtos que tiverem estoque disponivel para o B2B
class ProductsGallery(Resource):
    @ns_stock.response(HTTPStatus.OK.value,"Obtem a listagem de produto",prd_return)
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_stock.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_stock.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_stock.param("query","Texto com parametros para busca","query")
    @auth.login_required
    def get(self):
        pag_num    = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size   = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query      = "" if request.args.get("query") is None or request.args.get("query")=="" else request.args.get("query")

        try:
            params     =  _get_params(query)
            order_by   = "id" if hasattr(params,"order_by")  == False else params.order_by
            direction  = asc if hasattr(params,"order")      == False else asc if str(params.order).lower()=='asc' else desc
            list_all   = False if hasattr(params,"list_all") == False else True
            search     = None if hasattr(params,'search')    == False else "%{}%".format(params.search)

            filter_brand      = None if hasattr(params,"brand")      == False else params.brand
            filter_collection = None if hasattr(params,"collection") == False else params.collection
            filter_category   = None if hasattr(params,"category")   == False else params.category
            filter_model      = None if hasattr(params,"model")      == False else params.model
            filter_type       = None if hasattr(params,"type")       == False else params.type
            filter_color      = None if hasattr(params,"color")      == False else params.color
            filter_size       = None if hasattr(params,"size")       == False else params.size

            #realiza a busca das colecoes que tem restricao no calendario
            rquery = Select(CmmProducts.id,CmmProducts.id_grid,CmmProducts.prodCode,CmmProducts.barCode,
                            CmmProducts.refCode,CmmProducts.name,CmmProducts.description,CmmProducts.observation,
                            CmmProducts.ncm,CmmProducts.price,CmmMeasureUnit.code.label("measure_unit"),CmmProducts.structure,
                            CmmProducts.date_created,CmmProducts.date_updated,CmmCategories.name.label("category_name"),
                            B2bCollection.name.label("collection_name"),B2bBrand.name.label("brand_name"),
                            CmmProductsTypes.name.label("product_type_name"),CmmProductsModels.name.label("product_model_name"))\
                .join(CmmProductsTypes,CmmProductsTypes.id==CmmProducts.id_type)\
                .join(CmmProductsModels,CmmProductsModels.id==CmmProducts.id_model)\
                .join(CmmMeasureUnit,CmmMeasureUnit.id==CmmProducts.id_measure_unit)\
                .outerjoin(B2bTablePriceProduct,B2bTablePriceProduct.id_product==CmmProducts.id)\
                .outerjoin(B2bTablePrice,B2bTablePrice.id==B2bTablePriceProduct.id_table_price)\
                .outerjoin(B2bCollectionPrice,B2bCollectionPrice.id_table_price==B2bTablePrice.id)\
                .outerjoin(B2bCollection,B2bCollection.id==B2bCollectionPrice.id_collection)\
                .outerjoin(B2bBrand,B2bBrand.id==B2bCollection.id_brand)\
                .outerjoin(CmmProductsCategories,CmmProductsCategories.id_product==CmmProducts.id)\
                .outerjoin(CmmCategories,CmmCategories.id==CmmProductsCategories.id_category)\
                .where(CmmProducts.trash==False)\
                .where(CmmProducts.id.in_(
                    Select(B2bProductStock.id_product).where(
                        or_(
                            B2bProductStock.quantity > 0, #possui quantidade indiferente de tamanho e cor
                            and_( #produto ilimitado
                                B2bProductStock.quantity==0,
                                B2bProductStock.ilimited==True
                            )
                        )
                    ))
                ).where(
                    B2bCollection.id.in_(
                        Select(ScmEvent.id_collection).where(
                            and_( #esta dentro do periodo
                                ScmEvent.year==datetime.now().year,
                                ScmEvent.start_date >= datetime.now().isoformat()[0:10],
                                ScmEvent.end_date <= datetime.now().isoformat()[0:10]
                            )
                        )
                    )
                )
            
            #busca as colecoes que nao possuem restricao (irrestrict)
            iquery = Select(CmmProducts.id,CmmProducts.id_grid,CmmProducts.prodCode,CmmProducts.barCode,
                            CmmProducts.refCode,CmmProducts.name,CmmProducts.description,CmmProducts.observation,
                            CmmProducts.ncm,CmmProducts.price,CmmMeasureUnit.code.label("measure_unit"),CmmProducts.structure,
                            CmmProducts.date_created,CmmProducts.date_updated,CmmCategories.name.label("category_name"),
                            B2bCollection.name.label("collection_name"),B2bBrand.name.label("brand_name"),
                            CmmProductsTypes.name.label("product_type_name"),CmmProductsModels.name.label("product_model_name"))\
                .join(CmmProductsTypes,CmmProductsTypes.id==CmmProducts.id_type)\
                .join(CmmProductsModels,CmmProductsModels.id==CmmProducts.id_model)\
                .join(CmmMeasureUnit,CmmMeasureUnit.id==CmmProducts.id_measure_unit)\
                .outerjoin(B2bTablePriceProduct,B2bTablePriceProduct.id_product==CmmProducts.id)\
                .outerjoin(B2bTablePrice,B2bTablePrice.id==B2bTablePriceProduct.id_table_price)\
                .outerjoin(B2bCollectionPrice,B2bCollectionPrice.id_table_price==B2bTablePrice.id)\
                .outerjoin(B2bCollection,B2bCollection.id==B2bCollectionPrice.id_collection)\
                .outerjoin(B2bBrand,B2bBrand.id==B2bCollection.id_brand)\
                .outerjoin(CmmProductsCategories,CmmProductsCategories.id_product==CmmProducts.id)\
                .outerjoin(CmmCategories,CmmCategories.id==CmmProductsCategories.id_category)\
                .where(CmmProducts.trash==False)\
                .where(CmmProducts.id.in_(
                    Select(B2bProductStock.id_product).where(
                        or_(
                            B2bProductStock.quantity > 0, #possui quantidade indiferente de tamanho e cor
                            and_( #produto ilimitado
                                B2bProductStock.quantity==0,
                                B2bProductStock.ilimited==True
                            )
                        )
                    ))
                ).where(
                    B2bCollection.id.not_in(
                        Select(ScmEvent.id_collection).where(
                            and_( #que nao esta dentro do periodo
                                ScmEvent.year==datetime.now().year,
                                ScmEvent.start_date >= datetime.now().isoformat()[0:10],
                                ScmEvent.end_date <= datetime.now().isoformat()[0:10]
                            )
                        )
                    )
                )

            #color query
            cquery = Select(CmmTranslateColors.name,CmmTranslateColors.id,CmmTranslateColors.hexcode).distinct()\
                    .join(CmmProductsGridDistribution,CmmProductsGridDistribution.id_color==CmmTranslateColors.id)\
                    .join(CmmProductsGrid,CmmProductsGrid.id==CmmProductsGridDistribution.id_grid)
            
            if search is not None:
                rquery = rquery.where(and_(CmmProducts.trash==False,or_(
                    CmmProducts.name.like(search),
                    CmmProducts.description.like(search),
                    CmmProducts.barCode.like(search),
                    CmmProducts.observation.like(search),
                    CmmCategories.name.like(search),
                    CmmProductsModels.name.like(search),
                    CmmProductsTypes.name.like(search)
                )))

                iquery = iquery.where(and_(CmmProducts.trash==False,or_(
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
                rquery = rquery.where(CmmProducts.id_grid.in_(
                    Select(CmmProductsGridDistribution.id_color.in_(filter_color.split(",")))
                ))
                iquery = iquery.where(CmmProducts.id_grid.in_(
                    Select(CmmProductsGridDistribution.id_color.in_(filter_color.split(",")))
                ))
            
            if filter_size is not None:
                rquery = rquery.where(CmmProducts.id_grid.in_(
                    Select(CmmProductsGridDistribution.id_size.in_(filter_size.split(",")))
                ))
                iquery = iquery.where(CmmProducts.id_grid.in_(
                    Select(CmmProductsGridDistribution.id_size.in_(filter_size.split(",")))
                ))

            rquery = rquery.union(iquery)

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
                        "prodCode": m.prodCode,
                        "barCode": m.barCode,
                        "refCode": m.refCode,
                        "name": m.name,
                        "description": m.description,
                        "observation": m.observation,
                        "ncm": m.ncm,
                        "price": float(str(m.price)),
                        "measure_unit": m.measure_unit,
                        "structure": m.structure,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None,
                        "images": self.get_images(m.id),
                        "colors": [{
                            "id": c.id,
                            "name": c.name,
                            "color": c.hexcode
                        }for c in db.session.execute(cquery.where(CmmProductsGrid.id==m.id_grid))]
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
                        "measure_unit": m.measure_unit,
                        "structure": m.structure,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None,
                        "images": self.get_images(m.id),
                        "colors": [{
                            "id": c.id,
                            "name": c.name,
                            "color": c.hexcode
                        }for c in db.session.execute(cquery.where(CmmProductsGrid.id==m.id_grid))]
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