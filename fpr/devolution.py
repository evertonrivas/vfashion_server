from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import FprDevolution,FprDevolutionItem,B2bOrders,CmmProducts,CmmLegalEntities, FprReason, _get_params,db
from sqlalchemy import Delete, Select, desc, exc, asc
from auth import auth
from config import Config

ns_devolution = Namespace("devolution",description="Operações para manipular dados de devoluções")

#API Models
dev_pag_model = ns_devolution.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)
dev_model = ns_devolution.model(
    "Devolution",{
        "id": fields.Integer,
        "id_order": fields.String,
        "date": fields.Date
    }
)

dev_return = ns_devolution.model(
    "DevolutionReturn",{
        "pagination": fields.Nested(dev_pag_model),
        "data": fields.List(fields.Nested(dev_model))
    }
)

@ns_devolution.route("/")
class CategoryList(Resource):
    @ns_devolution.response(HTTPStatus.OK.value,"Obtem a listagem de devoluções",dev_return)
    @ns_devolution.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_devolution.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_devolution.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_devolution.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))

        try:
            params    = _get_params(request.args.get("query"))
            direction = asc if hasattr(params,'order')==False else asc if params.order=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            list_all  = False if hasattr(params,"list_all")==False else params.list_all
            trash     = False if hasattr(params,"trash")==False else True

            rquery = Select(FprDevolution.id,
                            FprDevolution.date,
                            FprDevolution.status,
                            B2bOrders.id,
                            B2bOrders.date,
                            CmmLegalEntities.fantasy_name)\
                        .join(B2bOrders,B2bOrders.id==FprDevolution.id_order)\
                        .join(CmmLegalEntities,CmmLegalEntities.id==B2bOrders.id_customer)\
                        .order_by(direction(getattr(FprDevolution,order_by)))
            
            if search is not None:
                rquery = rquery.where(CmmLegalEntities.fantasy_name.like('%{}%'.format(search)))

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
						"description": m.description,
						"date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
						"date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
					} for m in db.session.execute(rquery)]
				}
            else:
                retorno = [{
						"id": m.id,
						"description": m.description,
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

    @ns_devolution.response(HTTPStatus.OK.value,"Cria uma nova devolução")
    @ns_devolution.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo etapa de devolução!")
    @ns_devolution.doc(body=dev_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            reg = FprDevolution()
            reg.id_order = req["id_order"]
            reg.status   = 0
            db.session.add(reg)
            db.session.commit()

            for item in req["itens"]:
                dev_item = FprDevolutionItem()
                dev_item.id_product    = item["id_product"]
                dev_item.id_reason     = item["id_reason"]
                dev_item.picture_1     = item["picture_1"]
                dev_item.picture_2     = item["picture_2"]
                dev_item.picture_3     = item["picture_3"]
                dev_item.picture_4     = item["picture_4"]
                dev_item.id_devolution = reg.id
                db.session.add(dev_item)
            db.session.commit()

            return reg.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_devolution.response(HTTPStatus.OK.value,"Exclui os dados de uma devolução")
    @ns_devolution.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self)->bool:
        try:
            req = request.get_json()
            for id in req["ids"]:
                reg:FprDevolution = FprDevolution.query.get(id)
                reg.trash = req["toTrash"]
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_devolution.route("/<int:id>")
class CategoryApi(Resource):
    @ns_devolution.response(HTTPStatus.OK.value,"Obtem um registro de uma etapa de devolução",dev_model)
    @ns_devolution.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            devolution:FprDevolution = FprDevolution.query.get(id)
            dev_itens  = Select(CmmProducts.name,
                                FprReason.description,
                                FprDevolutionItem.status
                ).where(FprDevolutionItem.id_devolution==id)
            customer = db.session.execute(
                Select(CmmLegalEntities.fantasy_name,B2bOrders.date)\
                    .join(B2bOrders,B2bOrders.id_customer==CmmLegalEntities.id)\
                    .where(B2bOrders.id==devolution.id_order)
            ).first()

            return {
                "id": devolution.id,
                "id_order": devolution.id_order,
                "order_date": customer.date,
                "customer": customer.fantasy_name,
                "date_created": devolution.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": devolution.date_updated.strftime("%Y-%m-%d %H:%M:%S") if devolution.date_updated!=None else None,
                "items":[{
                    "id_product": i.id_product,
                    "name": i.name,
                    "status": i.status
                }for i in db.session.execute(dev_itens)]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
            

    @ns_devolution.response(HTTPStatus.OK.value,"Atualiza os dados de uma etapa de devolução")
    @ns_devolution.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            reg:FprDevolution = FprDevolution.query.get(id)
            reg.status = req["status"]
            db.session.commit()

            # apaga todos os itens para inclui-los novamente, isso serve para a edição de devolução
            # no front do lojista
            db.session.execute(Delete(FprDevolutionItem).where(FprDevolutionItem.id_devolution==id))
            db.session.commit()

            # grava todos os itens novamente
            for item in req["itens"]:
                dev_item = FprDevolutionItem()
                dev_item.id_product    = item["id_product"]
                dev_item.id_reason     = item["id_reason"]
                dev_item.picture_1     = item["picture_1"]
                dev_item.picture_2     = item["picture_2"]
                dev_item.picture_3     = item["picture_3"]
                dev_item.picture_4     = item["picture_4"]
                dev_item.id_devolution = id
                db.session.add(dev_item)
            db.session.commit()
            return True

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }