from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bCollection,B2bCollectionPrice,db
import sqlalchemy as sa
from sqlalchemy import exc
from auth import auth

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
    #@auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
            if search!="":
                rquery = B2bCollection.query.filter(sa.and_(B2bCollection.trash == False,B2bCollection.name.like(search))).paginate(page=pag_num,per_page=pag_size)
            else:
                rquery = B2bCollection.query.filter(B2bCollection.trash == False).paginate(page=pag_num,per_page=pag_size)

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
                    "table_prices": self.get_customers(m.id)
                } for m in rquery.items]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    def get_customers(self,id:int):
        rquery = B2bCollectionPrice.query.filter_by(id_collection = id)
        return [{
            "id": m.id_table_price
        } for m in rquery.items]

    @ns_collection.response(HTTPStatus.OK.value,"Cria uma nova coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_collection.doc(body=coll_model)
    #@auth.login_required
    def post(self)->int:
        try:
            req = request.get_json()
            col = B2bCollection()
            col.name = req.name
            db.session.add(col)
            db.session.commit()

            for cst in col.prices:
                colp = B2bCollectionPrice()
                colp.id_collection  = col.id
                colp.id_table_price = cst.id_table_price
                db.session.add(colp)
                db.session.commit()

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
    #@auth.login_required
    def get(self,id:int):
        try:
            cquery = B2bCollection.query.get(id)
            squery = B2bCollectionPrice.query.filter_by(id_customer = id)

            return {
                "id": cquery.id,
                "name": cquery.name,
                "need_approval": cquery.need_approval,
                "customers": [{
                    "id": m.id_table_price
                }for m in squery.items]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_collection.response(HTTPStatus.OK.value,"Atualiza os dados de uma coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_collection.doc(body=coll_model)
    #@auth.login_required
    def post(self,id:int)->bool:
        try:
            req = request.get_json()
            col = B2bCollection.query.get(id)
            col.name          = col.name if req.name is None else req.name
            col.trash         = col.trash if req.trash is None else req.trash
            db.session.commit()


            #apaga e recria os clientes dependentes
            db.session.delete(B2bCollectionPrice()).where(B2bCollectionPrice().id_id_collection==id)
            db.session.commit()

            for it in col.prices:
                colp = B2bCollectionPrice()
                colp.id_collection  = id
                colp.id_table_price = it.id_table_price
                db.session.add(colp)
                db.session.commit()

            return True
        except:
            return False
    
    @ns_collection.response(HTTPStatus.OK.value,"Exclui os dados de uma coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    #@auth.login_required
    def delete(self,id:int)->bool:
        try:
            grp = B2bCollection.query.get(id)
            grp.trash = True
            db.session.commit()
            return True
        except:
            return False
        

class ColletionPriceApi(Resource):

    @ns_collection.response(HTTPStatus.OK.value,"Adiciona uma tabela de preço em uma coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Falha ao adicionar preço!")
    @ns_collection.param("id_table_price","Código da tabela de preço","formData",required=True)
    @ns_collection.param("id_collection","Código da coleção","formData",required=True)
    def post(self):
        try:
            colp = B2bCollectionPrice()
            colp.id_collection  = int(request.form.get("id_collection"))
            colp.id_table_price = int(request.form.get("id_table_price"))
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

    @ns_collection.response(HTTPStatus.OK.value,"Remove uma tabela de preço em uma coleção")
    @ns_collection.response(HTTPStatus.BAD_REQUEST.value,"Falha ao adicionar preço!")
    @ns_collection.param("id_table_price","Código da tabela de preço","formData",required=True)
    @ns_collection.param("id_collection","Código da coleção","formData",required=True)
    def delete(self):
        try:
            grp = B2bCollection.query.get(id)
            db.session.delete(grp)
            db.session.commit()
            return True
        except:
            return False

ns_collection.add_resource(ColletionPriceApi,'/manage-price')