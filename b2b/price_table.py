from http import HTTPStatus
from flask import request
from flask_restx import Resource, Namespace, fields
from models import B2bTablePrice, B2bTablePriceProduct, _get_params, db
# from models import _show_query
import json
from sqlalchemy import Select, exc, desc, asc
from auth import auth
from decimal import Decimal
from os import environ

ns_price = Namespace("price-table",description="Operações para manipular dados de tabelas de preços")

prc_pag_model = ns_price.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

prc_prod_model = ns_price.model(
    "Products",{
        "id_product": fields.Integer,
        "price": fields.Fixed,
        "price_retail": fields.Fixed
    }
)

prc_model = ns_price.model(
    "TablePrice",{
        "id": fields.Integer,
        "name": fields.String,
        "start_date": fields.DateTime,
        "end_date": fields.DateTime,
        "active": fields.Boolean,
        "products": fields.List(fields.Nested(prc_prod_model))
    }
)

prc_return = ns_price.model(
    "TablePriceReturn",{
        "pagination": fields.Nested(prc_pag_model),
        "data": fields.List(fields.Nested(prc_model))
    }
)

@ns_price.route("/")
class PriceTableList(Resource):
    @ns_price.response(HTTPStatus.OK.value,"Obtem a listagem de pedidos",prc_return)
    @ns_price.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_price.param("page","Número da página de registros","query",type=int,required=True)
    @ns_price.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_price.param("query","Texto para busca","query")
    @ns_price.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_price.param("order_by","Campo de ordenacao","query")
    @ns_price.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])

    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else request.args.get("query")
        list_all = False if request.args.get("list_all") is None else True
        order_by   = "id" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc

        try:
            params    = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False or hasattr(params,"search")!="" else params.search
            trash     = True if hasattr(params,'active')==False else False if params.active=="0" else True #foi invertido
            list_all  = False if hasattr(params,'list_all')==False else True

            rquery = Select(B2bTablePrice.id,
                            B2bTablePrice.name,
                            B2bTablePrice.start_date,
                            B2bTablePrice.end_date,
                            B2bTablePrice.active,
                            B2bTablePrice.date_created,
                            B2bTablePrice.date_updated)\
                            .where(B2bTablePrice.active==trash)\
                            .order_by(direction(getattr(B2bTablePrice,order_by)))

            if search is not None:
                rquery = rquery.where(B2bTablePrice.name.like("%{}%".format(search)))

            if list_all==False:
                pag = db.paginate(rquery,page=pag_num,per_page=pag_size)
                rquery = rquery.limit(pag_size).offset((pag_num - 1) * pag_size)

                retorno = {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next
                    },
                    "data":[{
                        "id": m.id,
                        "name": m.name,
                        "start_date": m.start_date,
                        "end_date": m.end_date,
                        "active": m.active
                    }for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id": m.id,
                        "name": m.name,
                        "start_date": m.start_date,
                        "end_date": m.end_date,
                        "active": m.active
                    }for m in db.session.execute(rquery)]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_price.response(HTTPStatus.OK.value,"Cria um novo pedido")
    @ns_price.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar pedido!")
    @ns_price.doc(body=prc_model)
    @auth.login_required
    def post(self)->int:
        try:
            req = json.dumps(request.get_json())
            table = B2bTablePrice()
            table.name       = req.name
            table.start_date = req.start_date
            table.end_date   = req.end_date
            table.active     = req.active
            db.session.add(table)
            db.session.commit()           
            return table.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_price.response(HTTPStatus.OK.value,"Exclui os dados de um carrinho")
    @ns_price.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self)->bool:
        try:
            req = request.get_json()
            for id in req["ids"]:
                price = B2bTablePrice.query.get(id)
                price.active = False
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_price.route("/<int:id>")
@ns_price.param("id","Id do registro")
class PriceTableApi(Resource):
    
    @ns_price.response(HTTPStatus.OK.value,"Obtem os dados de um carrinho")
    @ns_price.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            rquery = B2bTablePrice.query.get(id)
            squery = Select(B2bTablePriceProduct.id_product,
                            B2bTablePriceProduct.price,
                            B2bTablePriceProduct.price_retail)\
                            .where(B2bTablePriceProduct.id_table_price==id)
            return {
                "id": rquery.id,
                "name": rquery.name,
                "start_date": rquery.start_date.strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": rquery.end_date.strftime("%Y-%m-%d %H:%M:%S"),
                "active": rquery.active,
                "date_created": rquery.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": rquery.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_price.response(HTTPStatus.OK.value,"Atualiza os dados de um pedido")
    @ns_price.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_price.doc(body=prc_model)
    @auth.login_required
    def post(self,id:int)->bool:
        try:
            req = json.dumps(request.get_json())
            price = B2bTablePrice.query.get(id)
            price.name       = price.name if req.name is None else req.name
            price.start_date = price.start_date if req.start_date is None else req.start_date
            price.end_date   = price.end_date if req.end_date is None else req.end_date
            price.active     = price.active   if req.active is None else req.active
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


class B2bTablePriceProductApi(Resource):

    @ns_price.response(HTTPStatus.OK.value,"Adiciona uma tabela de preço em uma coleção")
    @ns_price.response(HTTPStatus.BAD_REQUEST.value,"Falha ao adicionar preço!")
    @ns_price.param("id_table_price","Código da tabela de preço","formData",required=True)
    @ns_price.param("id_product","Código do produto","formData",required=True)
    @auth.login_required
    def post(self):
        try:
            colp = B2bTablePriceProduct()
            colp.id_product     = int(request.form.get("id_product"))
            colp.id_table_price = int(request.form.get("id_table_price"))
            colp.price          = Decimal(request.form.get("price"))
            colp.price_retail   = Decimal(request.form.get("price_retail"))
            colp.stock_quantity = int(request.form.get("stock_quantity"))
            db.session.add(colp)
            db.session.commit()
            return True
        except exc.DatabaseError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        pass

    @ns_price.response(HTTPStatus.OK.value,"Remove uma tabela de preço em uma coleção")
    @ns_price.response(HTTPStatus.BAD_REQUEST.value,"Falha ao adicionar preço!")
    @ns_price.param("id_table_price","Código da tabela de preço","formData",required=True)
    @ns_price.param("id_product","Código do produto","formData",required=True)
    @auth.login_required
    def delete(self):
        try:
            id_table_price = request.args.get("id_table_price")
            id_product  = request.args.get("id_colid_productlection")
            grp = B2bTablePriceProduct.query.get((id_table_price,id_product))
            db.session.delete(grp)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

ns_price.add_resource(B2bTablePriceProductApi,'/manage-product')