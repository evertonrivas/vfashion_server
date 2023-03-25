from http import HTTPStatus
import simplejson as json
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bBrand, B2bCollectionPrice, CmmProducts, CmmProductsCategory,\
    CmmProductsSku,CmmProductsImage, CmmProductsType, \
    CmmProductsModel, B2bCollection, B2bTablePrice, \
    B2bTablePriceProduct,db
from sqlalchemy import desc, exc, and_, asc,Select,or_
from auth import auth
from decimal import Decimal

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

prd_sku_model = ns_prod.model(
    "SKU",{
        "id_product": fields.Integer,
        "id_type": fields.Integer,
        "id_model": fields.Integer,
        "size": fields.String,
        "color": fields.String
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
        "sku": fields.List(fields.Nested(prd_sku_model)),
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
        pag_size = 4 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
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
                    "name": m.name,
                    "description": m.description,
                    "observation": m.observation,
                    "ncm": m.ncm,
                    "price": json.dumps(Decimal(m.price)),
                    "measure_unit": m.measure_unit,
                    "structure": m.structure,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None,
                    "sku": self.get_sku(m.id),
                    "images": self.get_images(m.id)
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
        }for m in rquery]
    

    def get_images(self,id:int):
        rquery = CmmProductsImage.query.filter_by(id_product=id)
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
    @auth.login_required
    def get(self,id:int):
        try:
            rquery = CmmProducts.query.get(id)
            squery = CmmProductsSku.query.filter_by(id_product=id)
            iquery = CmmProductsImage.query.filter_by(id_product=id)
            return {
                "id": rquery.id,
                "prodCode": rquery.prodCode,
                "barCode": rquery.barCode,
                "refCode": rquery.refCode,
                "name": rquery.Name,
                "description": rquery.description,
                "observation": rquery.observation,
                "ncm": rquery.ncm,
                "price": json.dumps(Decimal(rquery.price)),
                "measure_unit": rquery.measure_unit,
                "structure": rquery.structure,
                "date_created": rquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": rquery.date_updated.strftime("%Y-%m-%d %H:%M:%S") if rquery.date_updated!=None else None,
                "sku": [{
                    "id_type": m.id_type,
                    "id_model": m.id_model,
                    "color": m.color,
                    "size" : m.size
                }for m in squery],
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


from sqlalchemy.ext.declarative import DeclarativeMeta

class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

#busca especifica para a galeria de produtos do B2B, jah que precisa buscar mais coisas além do nome
class ProductsGallery(Resource):
    @ns_prod.response(HTTPStatus.OK.value,"Obtem a listagem de produto",prd_return)
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_prod.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_prod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_prod.param("collection","Código da coleção",type=int)
    @ns_prod.param("category","Código da categoria",type=int)
    @ns_prod.param("model","Código do modelo",type=int)
    @ns_prod.param("type","Código do tipo",type=int)
    @ns_prod.param("query","Texto para busca","query")
    @ns_prod.param("order_by","Campo de ordenacao","query")
    @ns_prod.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    #@auth.login_required
    def get(self):
        pag_num    = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size   = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search     = "" if request.args.get("query") is None or request.args.get("query")=="" else "{}%".format(request.args.get("query"))
        brand      = None if request.args.get("brand") is None else request.args.get("brand")
        collection = None if request.args.get("collection") is None else request.args.get("collection")
        category   = None if request.args.get("category") is None else request.args.get("category")
        model      = None if request.args.get("model") is None else request.args.get("model")
        type       = None if request.args.get("type") is None else request.args.get("type")
        color      = None if request.args.get("color") is None else request.args.get("color")
        size       = None if request.args.get("size") is None else request.args.get("size")
        order_by   = "id" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc

        try:
            query = Select(CmmProducts)\
                .join(CmmProductsCategory,CmmProducts.id_category==CmmProductsCategory.id)\
                .join(CmmProductsType,CmmProductsType.id==CmmProducts.id_type)\
                .join(CmmProductsModel,CmmProductsModel.id==CmmProducts.id_model)\
                .outerjoin(B2bTablePriceProduct,B2bTablePriceProduct.id_product==CmmProducts.id)\
                .outerjoin(B2bTablePrice,B2bTablePrice.id==B2bTablePriceProduct.id_table_price)\
                .outerjoin(B2bCollectionPrice,B2bCollectionPrice.id_table_price==B2bTablePrice.id)\
                .outerjoin(B2bCollection,B2bCollection.id==B2bCollectionPrice.id_collection)\
                .outerjoin(B2bBrand,B2bBrand.id==B2bCollection.id_brand)
            if search!="":
                query = query.where(or_(
                    CmmProducts.trash==False,
                    CmmProducts.name.like(search),
                    CmmProducts.description.like(search),
                    CmmProducts.barCode.like(search),
                    CmmProducts.observation.like(search),
                    CmmProductsCategory.name.like(search),
                    CmmProductsModel.name.like(search),
                    CmmProductsType.name.like(search)
                ))
            if brand!= None:       query = query.where(B2bBrand.id.in_(brand.split(',')))
            if collection != None: query = query.where(B2bCollection.id.in_(collection.split(",")))
            if category!= None:    query = query.where(CmmProductsCategory.id.in_(category.split(",")))
            if model!=None:        query = query.where(CmmProductsModel.id.in_(model.split(",")))
            if type != None:       query = query.where(CmmProductsType.id.in_(type.split(",")))

            query = query.order_by(direction(getattr(CmmProducts, order_by)))

            #print(query)

            rquery = db.paginate(query,page=pag_num,per_page=pag_size)

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
                    "name": m.name,
                    "description": m.description,
                    "observation": m.observation,
                    "ncm": m.ncm,
                    "price": json.dumps(Decimal(m.price)),
                    "measure_unit": m.measure_unit,
                    "structure": m.structure,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None,
                    "sku": self.get_sku(m.id),
                    "images": self.get_images(m.id)
                } for m in rquery]
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
        }for m in rquery]
    

    def get_images(self,id:int):
        rquery = CmmProductsImage.query.filter_by(id_product=id)
        return [{
            "id": m.id,
            "img_url":m.img_url
        }for m in rquery]


ns_prod.add_resource(ProductsGallery,'/gallery/')