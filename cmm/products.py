from datetime import datetime
from http import HTTPStatus
import simplejson
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmProducts, CmmProductsGrid, \
    CmmProductsImages, CmmProductsTypes, CmmProductsModels, \
    _get_params, db
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
        query   = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params = _get_params(query)
            trash     = False if hasattr(params,"trash")==False else True
            order_by  = "name" if hasattr(params,"order_by")==False else params.order_by
            direction = asc if hasattr(params,"order")==False else asc if str(params.order).lower()=="asc" else desc
        
            filter_search = None if hasattr(params,"search")==False else params.name
            filter_type   = None if hasattr(params,"type")==False else params.type
            filter_model  = None if hasattr(params,"model")==False else params.model
            filter_grid   = None if hasattr(params,"grid")==False else params.grid

            rquery = Select(CmmProducts.id,
                            CmmProducts.prodCode,
                            CmmProducts.barCode,
                            CmmProducts.refCode,
                            CmmProducts.name,
                            CmmProducts.description,
                            CmmProducts.observation,
                            CmmProducts.ncm,
                            CmmProducts.price,
                            CmmProducts.measure_unit,
                            CmmProducts.structure,
                            CmmProducts.date_created,
                            CmmProducts.date_updated,
                            CmmProductsTypes.name.label("type_description"),
                            CmmProductsModels.name.label("model_description"),
                            CmmProductsGrid.name.label("grid_description")
                            ).join(CmmProductsTypes,CmmProductsTypes.id==CmmProducts.id_type)\
                            .join(CmmProductsModels,CmmProductsModels.id==CmmProducts.id_model)\
                            .join(CmmProductsGrid,CmmProductsGrid.id==CmmProducts.id_grid)\
                            .where(CmmProducts.trash==trash)\
                            .order_by(direction(getattr(CmmProducts, order_by)))
            
            if filter_search is not None:
                rquery.where(or_(
                    CmmProducts.name.like("%{}%".format(filter_search)),
                    CmmProducts.description.like("%{}%".format(filter_search)),
                    CmmProducts.observation.like("%{}%".format(filter_search)),
                    CmmProducts.barCode.like("%{}%".format(filter_search)),
                    CmmProducts.refCode.like("%{}%".format(filter_search))
                ))

            if filter_model is not None:
                rquery.where(CmmProducts.id_model==filter_model)

            if filter_type is not None:
                rquery.where(CmmProducts.id_type==filter_type)

            if filter_grid is not None:
                rquery.where(CmmProducts.id_grid==filter_grid)

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
                        "measure_unit": m.measure_unit,
                        "structure": m.structure,
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
                        "measure_unit": m.measure_unit,
                        "structure": m.structure,
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
        
    @ns_prod.response(HTTPStatus.OK.value,"Exclui os dados de produto(s)")
    @ns_prod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def delete(self)->bool:
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
