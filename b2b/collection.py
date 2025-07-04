from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bBrand, B2bCollection, _get_params,db
# from models import _show_query
from sqlalchemy import Select, exc, desc, asc
from auth import auth
from os import environ

ns_collection = Namespace("collection",description="Operações para manipular dados de coleções")

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR AS COLEÇÕES DE PRODUTOS            #
####################################################################################

coll_pag_model = ns_collection.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

prc_id_model = ns_collection.model(
    "PriceTable",{
        "id": fields.Integer
    }
)

coll_model = ns_collection.model(
    "Collection",{
        "id": fields.Integer,
        "name": fields.String,
        "table_prices": fields.List(fields.Nested(prc_id_model))
    }
)

coll_return = ns_collection.model(
    "CollectionReturn",{
        "pagination": fields.Nested(coll_pag_model),
        "data": fields.List(fields.Nested(coll_model))
    }
)



@ns_collection.route("/")
class CollectionList(Resource):
    @ns_collection.response(HTTPStatus.OK.value,"Obtem um registro de uma coleção",coll_return)
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_collection.param("page","Número da página de registros","query",type=int,required=True)
    @ns_collection.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_collection.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            trash     = False if hasattr(params,'active')==False else True
            list_all  = False if hasattr(params,'list_all')==False else True

            filter_brand = None if hasattr(params,'brand')==False or (hasattr(params,'brand')==True and params.brand==0) else params.brand

            rquery = Select(B2bCollection.id,
                            B2bCollection.id_brand,
                            B2bCollection.name,
                            B2bCollection.date_created,
                            B2bCollection.date_updated,
                            B2bBrand.name.label("brand"))\
                            .join(B2bBrand,B2bBrand.id==B2bCollection.id_brand)\
                            .where(B2bCollection.trash==trash)\
                            .order_by(direction(getattr(B2bCollection,order_by)))
            
            if search is not None:
                rquery = rquery.where(B2bCollection.name.like("%{}%".format(search)))

            if filter_brand is not None:
                rquery = rquery.where(B2bCollection.id_brand==filter_brand)


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
                        "brand":{
                            "id_brand": m.id_brand,
                            "name": m.brand
                        },
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id":m.id,
                        "name":m.name,
                        "brand": {
                            "id_brand": m.id_brand,
                            "name": m.brand
                        },
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_collection.response(HTTPStatus.OK.value,"Cria uma nova coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_collection.doc(body=coll_model)
    @auth.login_required
    def post(self)->int:
        try:
            req = request.get_json()
            col = B2bCollection()
            col.name = req["name"]
            col.id_brand = req["id_brand"]
            db.session.add(col)
            db.session.commit()

            # for cst in col.prices:
            #     colp = B2bCollectionPrice()
            #     colp.id_collection  = col.id
            #     colp.id_table_price = cst.id_table_price
            #     db.session.add(colp)
            #     db.session.commit()

            return col.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_collection.route("/<int:id>")
@ns_collection.param("id","Id do registro")
class CollectionApi(Resource):
    @ns_collection.response(HTTPStatus.OK.value,"Retorna os dados dados de uma coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            cquery = db.session.execute(Select(B2bCollection.id,
                            B2bCollection.name,
                            B2bCollection.date_created,
                            B2bCollection.date_created,
                            B2bCollection.id_brand,
                            B2bBrand.name.label("brand"))\
                            .join(B2bBrand,B2bBrand.id==B2bCollection.id_brand)\
                            .where(B2bCollection.id==id)).first()

            return {
                "id": cquery.id,
                "name": cquery.name,
                "brand":{
                    "id": cquery.id_brand,
                    "name": cquery.brand
                }
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_collection.response(HTTPStatus.OK.value,"Exclui os dados de uma coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self)->bool:
        try:
            req = request.get_json()
            for id in req["ids"]:
                grp = B2bCollection.query.get(id)
                grp.trash = True
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_collection.response(HTTPStatus.OK.value,"Atualiza os dados de uma coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_collection.doc(body=coll_model)
    @auth.login_required
    def post(self,id:int)->bool:
        try:
            req = request.get_json()
            col:B2bCollection = B2bCollection.query.get(id)
            col.name     = req["name"]
            col.id_brand = req["id_brand"]
            db.session.commit()


            #apaga e recria os clientes dependentes
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }