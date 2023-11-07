from datetime import datetime
from http import HTTPStatus
import simplejson
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bBrand, B2bCollectionPrice, B2bProductStock, CmmCategories, CmmProducts, CmmProductsCategories, CmmProductsGrid, CmmProductsGridDistribution,\
    CmmProductsImages, CmmProductsTypes, \
    CmmProductsModels, B2bCollection, B2bTablePrice, \
    B2bTablePriceProduct, CmmTranslateColors,CmmTranslateSizes, ScmCalendar, ScmEvent, _get_params, _show_query, db
from sqlalchemy import desc, exc, and_, asc,Select, func,or_
from auth import auth
from decimal import Decimal
from config import Config

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
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        order_by = "name" if request.args.get("order_by") is None else request.args.get("order_by")
        direction = asc if request.args.get("order_dir") == 'ASC' else desc

        try:
            if search!="":
                rquery = CmmProducts\
                    .query\
                    .filter(and_(CmmProducts.trash==False,CmmProducts.name.like(search)))\
                    .order_by(direction(getattr(CmmProducts, order_by)))\
                    .paginate(page=pag_num,per_page=pag_size)
            else:
                rquery = CmmProducts\
                    .query\
                    .filter(CmmProducts.trash==False)\
                    .order_by(direction(getattr(CmmProducts, order_by)))\
                    .paginate(page=pag_num,per_page=pag_size)

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
                    "id_category": m.id_category,
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
                    "images": self.get_images(m.id)
                } for m in rquery.items]
            }
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
            "img_url":m.img_url
        }for m in rquery]

    @ns_prod.response(HTTPStatus.OK.value,"Cria um novo produto no sistema")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo produto!")
    @ns_prod.doc(body=prd_model)
    @auth.login_required
    def post(self)->int:
        try:
            req = simplejson.dumps(request.get_json())
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
    @auth.login_required
    def get(self,id:int):
        try:
            rquery = CmmProducts.query.get(id)
            iquery = CmmProductsImages.query.filter_by(id_product=id)
            return {
                "id": rquery.id,
                "prodCode": rquery.prodCode,
                "barCode": rquery.barCode,
                "refCode": rquery.refCode,
                "name": rquery.name,
                "description": rquery.description,
                "observation": rquery.observation,
                "ncm": rquery.ncm,
                "price": simplejson.dumps(Decimal(rquery.price)),
                "measure_unit": rquery.measure_unit,
                "structure": rquery.structure,
                "date_created": rquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": rquery.date_updated.strftime("%Y-%m-%d %H:%M:%S") if rquery.date_updated!=None else None,
                "images":[{
                    "id": m.id,
                    "img_url": m.img_url
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
    def post(self,id:int)->bool:
        try:
            req = request.get_json()
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
            prod.price         = prod.price if req.price is None else float(req.price)
            prod.measure_unit  = prod.measure_unit if req.measure_unit is None else req.measure_unit
            prod.trash         = prod.trash if req.trash is None else req.trash
            db.session.commit()

            #apaga todos as imagens registradas e realiza novo registro
            #eh mais facil do que realizar testes para saber se saiu ou entrou registro
            db.session.delete(CmmProductsImages()).where(CmmProductsImages().id_product==id)
            db.session.commit()
            for s in req.images:
                img = CmmProductsImages()
                img.id_product = id
                img.img_url    = s.img_url
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


#busca especifica para a galeria de produtos do B2B, jah que precisa buscar mais coisas além do nome
#so irah buscar produtos que tiverem estoque disponivel para o B2B
class ProductsGallery(Resource):
    @ns_prod.response(HTTPStatus.OK.value,"Obtem a listagem de produto",prd_return)
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_prod.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_prod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_prod.param("query","Texto com parametros para busca","query")
    @auth.login_required
    def get(self):
        pag_num    = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size   = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query      = "" if request.args.get("query") is None or request.args.get("query")=="" else request.args.get("query")

        try:
            params     =  _get_params(query)
            order_by   = "id" if hasattr(params,"order_by")==False else params.order_by
            direction  = asc if hasattr(params,"order")==False else asc if str(params.order).lower()=='asc' else desc
            list_all   = False if hasattr(params,"list_all")==False else True
            search     = None if hasattr(params,'search')==False else "%{}%".format(params.search)

            filter_brand      = None if hasattr(params,"brand") == False else params.brand
            filter_collection = None if hasattr(params,"collection") == False else params.collection
            filter_category   = None if hasattr(params,"category") == False else params.category
            filter_model      = None if hasattr(params,"model") == False else params.model
            filter_type       = None if hasattr(params,"type") == False else params.type
            filter_color      = None if hasattr(params,"color") == False else params.color
            filter_size       = None if hasattr(params,"size") == False else params.size

            #realiza a busca das colecoes que tem restricao no calendario
            rquery = Select(CmmProducts.id,CmmProducts.id_grid,CmmProducts.prodCode,CmmProducts.barCode,
                            CmmProducts.refCode,CmmProducts.name,CmmProducts.description,CmmProducts.observation,
                            CmmProducts.ncm,CmmProducts.price,CmmProducts.measure_unit,CmmProducts.structure,
                            CmmProducts.date_created,CmmProducts.date_updated,CmmCategories.name.label("category_name"),
                            B2bCollection.name.label("collection_name"),B2bBrand.name.label("brand_name"),
                            CmmProductsTypes.name.label("product_type_name"),CmmProductsModels.name.label("product_model_name"))\
                .join(CmmProductsTypes,CmmProductsTypes.id==CmmProducts.id_type)\
                .join(CmmProductsModels,CmmProductsModels.id==CmmProducts.id_model)\
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
                            B2bProductStock.quantity > 0,
                            and_(
                                B2bProductStock.quantity==0,
                                B2bProductStock.ilimited==True
                            )
                        )
                    ))
                ).where(
                    B2bCollection.id.in_(
                        Select(ScmEvent.id_collection).where(
                            and_(
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
                            CmmProducts.ncm,CmmProducts.price,CmmProducts.measure_unit,CmmProducts.structure,
                            CmmProducts.date_created,CmmProducts.date_updated,CmmCategories.name.label("category_name"),
                            B2bCollection.name.label("collection_name"),B2bBrand.name.label("brand_name"),
                            CmmProductsTypes.name.label("product_type_name"),CmmProductsModels.name.label("product_model_name"))\
                .join(CmmProductsTypes,CmmProductsTypes.id==CmmProducts.id_type)\
                .join(CmmProductsModels,CmmProductsModels.id==CmmProducts.id_model)\
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
                            B2bProductStock.quantity > 0,
                            and_(
                                B2bProductStock.quantity==0,
                                B2bProductStock.ilimited==True
                            )
                        )
                    ))
                ).where(
                    B2bCollection.id.not_in(
                        Select(ScmEvent.id_collection).where(
                            and_(
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
                    CmmProductsCategories.name.like(search),
                    CmmProductsModels.name.like(search),
                    CmmProductsTypes.name.like(search)
                )))

                iquery = iquery.where(and_(CmmProducts.trash==False,or_(
                    CmmProducts.name.like(search),
                    CmmProducts.description.like(search),
                    CmmProducts.barCode.like(search),
                    CmmProducts.observation.like(search),
                    CmmProductsCategories.name.like(search),
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

            # print("Query de produtos \n\n\n")
            # _show_query(rquery)

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

ns_prod.add_resource(ProductsGallery,'/gallery/')