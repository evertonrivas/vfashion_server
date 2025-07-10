from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.helpers import db
# from models import _show_query
from f2bconfig import OrderStatus
from flask_restx import Resource,Namespace,fields
from sqlalchemy import Delete, Select, exc,and_,desc,asc, func
from models.tenant import B2bCustomerGroup,B2bCustomerGroupCustomers, B2bOrders, CmmLegalEntities, _get_params

ns_customer_g = Namespace("customer-group",description="Operações para manipular dados de grupos de clientes")

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CLIENTES              #
####################################################################################

grp_pag_model = ns_customer_g.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

grp_model = ns_customer_g.model(
    "CustomerGroup",{
        "id_customer": fields.Integer,
        "id_representative": fields.String,
        "need_approvement": fields.Integer,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime,
    }
)

coll_return = ns_customer_g.model(
    "CollectionReturn",{
        "pagination": fields.Nested(grp_pag_model),
        "data": fields.List(fields.Nested(grp_model))
    }
)



@ns_customer_g.route("/")
class CollectionList(Resource):
    @ns_customer_g.response(HTTPStatus.OK.value,"Obtem um registro de uma coleção",coll_return)
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_customer_g.param("page","Número da página de registros","query",type=int,required=True)
    @ns_customer_g.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_customer_g.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params = _get_params(str(query))
            if params is not None:
                direction = asc if not hasattr(params,'order') else asc if str(params.order).upper()=='ASC' else desc
                order_by = 'id' if not hasattr(params,'order_by') else params.order_by
                search = None if not hasattr(params,"search") else params.search
                trash = False if not hasattr(params,'active') else True
                list_all = False if not hasattr(params,'list_all') else True

                filter_need_approvement = None if not hasattr(params,"need_approvement") else False if params.need_approvement==0 else True

            rquery = Select(B2bCustomerGroup.id,
                            B2bCustomerGroup.name,
                            B2bCustomerGroup.need_approvement,
                            B2bCustomerGroup.date_created,
                            B2bCustomerGroup.date_updated,
                            B2bCustomerGroup.id_representative,
                            CmmLegalEntities.name.label("representative"))\
                            .outerjoin(CmmLegalEntities,CmmLegalEntities.id==B2bCustomerGroup.id_representative)\
                            .where(B2bCustomerGroup.trash==trash)\
                            .order_by(direction(getattr(B2bCustomerGroup,order_by)))
            
            if search is not None:
                rquery = rquery.where(B2bCustomerGroup.name.like("%{}%".format(search)))

            if filter_need_approvement is not None:
                rquery = rquery.where(B2bCustomerGroup.need_approvement==filter_need_approvement)

            if not list_all:
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
                        "id_representative": m.id_representative,
                        "representative": m.representative,
                        "need_approvement": m.need_approvement,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                retorno = [{
                        "id":m.id,
                        "name":m.name,
                        "id_representative": m.id_representative,
                        "representative": m.representative,
                        "need_approvement": m.need_approvement,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_customer_g.response(HTTPStatus.OK.value,"Cria uma nova coleção")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar registro!")
    @ns_customer_g.doc(body=grp_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            grp = B2bCustomerGroup()
            grp.name = req["name"]
            setattr(grp,"id_representative",(None if req["id_representative"]=="null" or req["id_representative"]=="undefined" or req["id_representative"] is None else int(req["id_representative"])))
            setattr(grp,"need_approvement",int(req["need_approvement"]))
            db.session.add(grp)
            db.session.commit()

            return grp.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_customer_g.response(HTTPStatus.OK.value,"Exclui os dados de uma coleção")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                grp = B2bCustomerGroup.query.get(id)
                setattr(grp,"trash",True)
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_customer_g.route("/<int:id>")
@ns_customer_g.param("id","Id do registro")
class CollectionApi(Resource):
    @ns_customer_g.response(HTTPStatus.OK.value,"Retorna os dados dados de uma coleção")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            cquery = B2bCustomerGroup.query.get(id)

            return {
                "id": 0 if cquery is None else cquery.id,
                "name": "" if cquery is None else cquery.name,
                "id_representative": 0 if cquery is None else cquery.id_representative,
                "need_approvement": False if cquery is None else cquery.need_approvement
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_customer_g.response(HTTPStatus.OK.value,"Atualiza os dados de um grupo de clientes")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_customer_g.doc(body=grp_model)
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            grp:B2bCustomerGroup = B2bCustomerGroup.query.get(id) # type: ignore
            grp.name = req["name"]
            setattr(grp,"id_representative",(None if req["id_representative"]=="null" or req["id_representative"]=="undefined" or req["id_representative"] is None else int(req["id_representative"])))
            setattr(grp,"need_approvement",int(req["need_approvement"]))
            db.session.add(grp)
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_customer_g.response(HTTPStatus.OK.value,"Adiciona os clientes em um grupo")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_customer_g.doc(body=grp_model)
    @auth.login_required
    def put(self,id:int):
        try:
            req = request.get_json()

            #apaga o grupo onde cada usuario se encontra
            db.session.execute(
                Delete(B2bCustomerGroupCustomers).where(B2bCustomerGroupCustomers.id_customer.in_(req["ids"]))
            )
            db.session.commit()

            for id_customer in req["ids"]:
                grp:B2bCustomerGroupCustomers = B2bCustomerGroupCustomers() # type: ignore
                setattr(grp,"id_customer_group",id)
                grp.id_customer = id_customer
                db.session.add(grp)
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

class CustomersApi(Resource):
    @ns_customer_g.response(HTTPStatus.OK.value,"Obtem os clientes que compoem uma colecao")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_customer_g.param("page","Número da página de registros","query",type=int,required=True)
    @ns_customer_g.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_customer_g.param("query","Texto para busca","query")
    def get(self):
        pag_num =  1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query = "" if request.args.get("query") is None else request.args.get("query")

        try:
            #filter_id_group
            params = _get_params(str(query))
            if params is not None:
                filter_id_group = None if not hasattr(params,'id_group') else params.id_group

            # print(filter_id_group)

            rquery = Select(CmmLegalEntities.name,
                            B2bCustomerGroupCustomers.id_customer)\
                            .join(B2bCustomerGroupCustomers,B2bCustomerGroupCustomers.id_customer==CmmLegalEntities.id)\
                            .order_by(asc(CmmLegalEntities.name))
            
            if filter_id_group is not None:
                rquery = rquery.where(B2bCustomerGroupCustomers.id_customer_group==filter_id_group)

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
                        "id": m.id_customer,
                        "name": m.name
                    } for m in db.session.execute(rquery)]
                }

        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

ns_customer_g.add_resource(CustomersApi,'/customers/')


class CustomerRepresentative(Resource):
    @ns_customer_g.response(HTTPStatus.OK.value,"Obtem os clientes pertencentes a um representante")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            stmt = Select(func.count(B2bCustomerGroup.id).label("total")).select_from(B2bCustomerGroup)\
            .join(B2bCustomerGroupCustomers,B2bCustomerGroupCustomers.id_customer_group==B2bCustomerGroup.id)\
            .where(B2bCustomerGroup.id_representative==id)

            result = db.session.execute(stmt).first()
            total  = 0 if result is None or result.total is None else result.total

            return total
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_customer_g.response(HTTPStatus.OK.value,"Obtem o valor total em pedidos que os clientes do representante fizeram")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def post(self,id:int):
        try:
            stmt = Select(func.sum(B2bOrders.total_value).label("total"))\
            .join(B2bCustomerGroupCustomers,B2bCustomerGroupCustomers.id_customer==B2bOrders.id_customer)\
            .join(B2bCustomerGroup,B2bCustomerGroup.id==B2bCustomerGroupCustomers.id_customer_group)\
            .where(
                and_(
                    B2bCustomerGroup.id_representative==id,
                    B2bOrders.status==OrderStatus.FINISHED
                )
            )

            result = db.session.execute(stmt).first()
            total  = 0 if result is None or result.total is None else result.total

            return total
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_customer_g.response(HTTPStatus.OK.value,"Obtem o total de pedidos finalizados que os clientes do representante fizeram")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def put(self,id:int):
        try:
            stmt = Select(func.count(B2bOrders.id).label("total"))\
            .join(B2bCustomerGroupCustomers,B2bCustomerGroupCustomers.id_customer==B2bOrders.id_customer)\
            .join(B2bCustomerGroup,B2bCustomerGroup.id==B2bCustomerGroupCustomers.id_customer_group)\
            .where(
                and_(
                    B2bCustomerGroup.id_representative==id,
                    B2bOrders.status==OrderStatus.FINISHED
                )
            )

            result = db.session.execute(stmt).first()
            total  = 0 if result is None or result.total is None else result.total

            return total
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_customer_g.response(HTTPStatus.OK.value,"Obtem o valor da comissão que o representante tem a receber")
    @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    def patch(self,id:int):
        try:
            return id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
ns_customer_g.add_resource(CustomerRepresentative,'/representative-indicator/<int:id>')


# class ColletionPriceApi(Resource):

#     @ns_customer_g.response(HTTPStatus.OK.value,"Adiciona uma tabela de preço em uma coleção")
#     @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Falha ao adicionar preço!")
#     @ns_customer_g.param("id_table_price","Código da tabela de preço","formData",required=True)
#     @ns_customer_g.param("id_collection","Código da coleção","formData",required=True)
#     @auth.login_required
#     def post(self):
#         try:
#             colp = B2bCollectionPrice()
#             colp.id_collection  = int(request.form.get("id_collection"))
#             colp.id_table_price = int(request.form.get("id_table_price"))
#             db.session.add(colp)
#             db.session.commit()
#             return True
#         except exc.DatabaseError as e:
#             return {
#                 "error_code": e.code,
#                 "error_details": e._message(),
#                 "error_sql": e._sql_message()
#             }
#         pass

#     @ns_customer_g.response(HTTPStatus.OK.value,"Remove uma tabela de preço em uma coleção")
#     @ns_customer_g.response(HTTPStatus.BAD_REQUEST.value,"Falha ao adicionar preço!")
#     @ns_customer_g.param("id_table_price","Código da tabela de preço","formData",required=True)
#     @ns_customer_g.param("id_collection","Código da coleção","formData",required=True)
#     @auth.login_required
#     def delete(self):
#         try:
#             grp = B2bCollection.query.get(id)
#             db.session.delete(grp)
#             db.session.commit()
#             return True
#         except exc.SQLAlchemyError as e:
#             return {
#                 "error_code": e.code,
#                 "error_details": e._message(),
#                 "error_sql": e._sql_message()
#             }

# ns_customer_g.add_resource(ColletionPriceApi,'/manage-price')