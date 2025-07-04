from datetime import datetime
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmTranslateColors, CmmTranslateSizes, FprDevolution, FprDevolutionItem, B2bOrders, CmmProducts, CmmLegalEntities, FprReason, _get_params, _save_log, db
# from models import _show_query
from sqlalchemy import Delete, Select, Update, desc, distinct, exc, asc, func, text, tuple_
from auth import auth
from f2bconfig import CustomerAction, DevolutionStatus
from os import environ

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
        pag_num  = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))

        try:
            params    = _get_params(request.args.get("query"))
            direction = asc if hasattr(params,'order')==False else asc if params.order=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            list_all  = False if hasattr(params,"list_all")==False else params.list_all
            trash     = False if hasattr(params,"trash")==False else True
            no_status = None if hasattr(params,"no_status")==False else params.no_status

            rquery = Select(FprDevolution.id,
                            FprDevolution.date,
                            FprDevolution.status,
                            B2bOrders.id.label("id_order"),
                            B2bOrders.date.label("order_date"),
                            CmmLegalEntities.fantasy_name)\
                        .join(B2bOrders,B2bOrders.id==FprDevolution.id_order)\
                        .join(CmmLegalEntities,CmmLegalEntities.id==B2bOrders.id_customer)\
                        .where(FprDevolution.trash==trash)\
                        .order_by(direction(getattr(FprDevolution,order_by)))
            
            if search is not None:
                rquery = rquery.where(CmmLegalEntities.fantasy_name.like('%{}%'.format(search)))

            if no_status is not None:
                rquery = rquery.where(FprDevolution.status!=no_status)

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
						"id": '{:010d}'.format(m.id),
						"date": m.date.strftime("%Y-%m-%d"),
                        "id_order": '{:010d}'.format(m.id_order),
                        "order_date": m.order_date.strftime("%Y-%m-%d"),
                        "customer": m.fantasy_name,
                        "status": m.status
					} for m in db.session.execute(rquery)]
				}
            else:
                retorno = [{
						"id": '{:010d}'.format(m.id),
						"date": m.date.strftime("%Y-%m-%d"),
                        "id_order": '{:010d}'.format(m.id_order),
                        "order_date": m.order_date.strftime("%Y-%m-%d"),
                        "customer": m.fantasy_name,
                        "status": m.status
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
            reg.status   = req["status"]
            reg.date = datetime.now()
            db.session.add(reg)
            db.session.commit()

            for item in req["items"]:
                dev_item = FprDevolutionItem()
                dev_item.id_product    = item["id_product"]
                dev_item.id_color      = item["id_color"]
                dev_item.id_size       = item["id_size"]
                dev_item.id_reason     = item["id_reason"]
                dev_item.quantity      = item["quantity"]
                dev_item.picture_1     = None if "picture_1" not in item else item["picture_1"]
                dev_item.picture_2     = None if "picture_2" not in item else item["picture_2"]
                dev_item.picture_3     = None if "picture_3" not in item else item["picture_3"]
                dev_item.picture_4     = None if "picture_4" not in item else item["picture_4"]
                dev_item.id_devolution = reg.id
                db.session.add(dev_item)
            db.session.commit()

            _save_log(B2bOrders.query.get(req["id_order"]).id_customer,
                      CustomerAction.RETURN_CREATED,
                      'Nova devolucao ('+str('{:010d}'.format(reg.id))+') realizada - em '+datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

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
            dev_itens  = Select(FprDevolutionItem.id_devolution,
                                CmmProducts.name.label("name_product"),
                                FprDevolutionItem.id_product,
                                FprDevolutionItem.id_color,
                                CmmTranslateColors.name.label("name_color"),
                                FprDevolutionItem.id_size,
                                CmmTranslateSizes.new_size.label("name_size"),
                                FprDevolutionItem.id_reason,
                                FprReason.description,
                                FprDevolutionItem.quantity,
                                FprDevolutionItem.status,
                                FprDevolutionItem.picture_1,
                                FprDevolutionItem.picture_2,
                                FprDevolutionItem.picture_3,
                                FprDevolutionItem.picture_4
                )\
                .join(CmmProducts,CmmProducts.id==FprDevolutionItem.id_product)\
                .join(CmmTranslateColors,CmmTranslateColors.id==FprDevolutionItem.id_color)\
                .join(CmmTranslateSizes,CmmTranslateSizes.id==FprDevolutionItem.id_size)\
                .join(FprReason,FprReason.id==FprDevolutionItem.id_reason)\
                .where(FprDevolutionItem.id_devolution==id)
            customer = db.session.execute(
                Select(CmmLegalEntities.fantasy_name,B2bOrders.date)\
                    .join(B2bOrders,B2bOrders.id_customer==CmmLegalEntities.id)\
                    .where(B2bOrders.id==devolution.id_order)
            ).first()

            return {
                "id": devolution.id,
                "date": devolution.date.strftime("%Y-%m-%d"),
                "id_order": devolution.id_order,
                "order_date": customer.date.strftime("%Y-%m-%d"),
                "status": devolution.status,
                "customer": customer.fantasy_name,
                "date_created": devolution.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": devolution.date_updated.strftime("%Y-%m-%d %H:%M:%S") if devolution.date_updated!=None else None,
                "items":[{
                    "id_devolution_item": str(i.id_product)+'_'+str(i.id_color)+'_'+str(i.id_size),
                    "name_product": i.name_product,
                    "id_product": i.id_product,
                    "name_color": i.name_color,
                    "id_color": i.id_color,
                    "name_size": i.name_size,
                    "id_size": i.id_size,
                    "quantity": i.quantity,
                    "reason": i.description,
                    "id_reason": i.id_reason,
                    "status": i.status,
                    "picture_1": i.picture_1,
                    "picture_2": i.picture_2,
                    "picture_3": i.picture_3,
                    "picture_4": i.picture_4
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

            # apaga todos os itens para inclui-los novamente, isso serve para a edição de devolução
            # no front do lojista
            db.session.execute(Delete(FprDevolutionItem).where(FprDevolutionItem.id_devolution==id))
            db.session.commit()

            approved = 0
            reproved = 0
            # grava todos os itens novamente
            for item in req["items"]:
                dev_item = FprDevolutionItem()
                dev_item.id_product    = item["id_product"]
                dev_item.id_color      = item["id_color"]
                dev_item.id_size       = item["id_size"]
                dev_item.id_reason     = item["id_reason"]
                dev_item.quantity      = item["quantity"]
                dev_item.picture_1     = item["picture_1"]
                dev_item.picture_2     = item["picture_2"]
                dev_item.picture_3     = item["picture_3"]
                dev_item.picture_4     = item["picture_4"]
                dev_item.status        = item["status"]
                dev_item.id_devolution = id
                approved += 1 if item["status"]==True else 0
                reproved += 1 if item["status"]==False else 0
                db.session.add(dev_item)
            db.session.commit()

            # atualiza o status da devolucao para que o cliente tenha parcepcao
            reg:FprDevolution = FprDevolution.query.get(id)
            if approved==len(req["items"]):
                reg.status = DevolutionStatus.APPROVED_ALL.value
            elif (approved+reproved)==len(req["items"]):
                reg.status = DevolutionStatus.APPROVED_PART.value
            elif reproved == len(req["items"]):
                reg.status = DevolutionStatus.REJECTED.value
            db.session.commit()

            id_customer = db.session.execute(
                Select(B2bOrders.id_customer)\
                .join(FprDevolution,FprDevolution.id_order==B2bOrders.id)\
                .where(FprDevolution.id==id)
            ).first().id_customer

            _save_log(id_customer,
                      CustomerAction.RETURN_UPDATED,
                      'Devolução ('+str('{:010d}'.format(reg.id))+') atualizada - em '+datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_devolution.response(HTTPStatus.OK.value,"Finaliza o status de uma devolução")
    @ns_devolution.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def put(self,id:int):
        try:
            db.session.execute(
                Update(FprDevolution).values(status=DevolutionStatus.FINISHED.value).where(FprDevolution.id==id)
            )
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
@ns_devolution.param('id_entity','Código do perfil',"query",type=int)
class DevolutionTotal(Resource):
    @ns_devolution.response(HTTPStatus.OK.value,"Lista o total de produtos no carrinho")
    @ns_devolution.response(HTTPStatus.BAD_REQUEST.value,"Falha ao contar registros!")
    @ns_devolution.param("userType","Tipo do usuário","query",enum=['A','L','I','R'])
    @auth.login_required
    def get(self,id_entity:int):

        userType = request.args.get("userType")

        query = Select(
            func.count(distinct(tuple_(FprDevolution.id))).label("total"))\
            .select_from(FprDevolution).where(FprDevolution.status.in_([
                        DevolutionStatus.APPROVED_ALL.value,
                        DevolutionStatus.APPROVED_PART.value,
                        DevolutionStatus.PENDING.value
                    ]))
            
        if userType=='L' or userType=='I':
            #aqui precisa buscar todos os os do representante
            query = query.where(FprDevolution.id_order.in_(
                Select(B2bOrders.id).where(B2bOrders.id_customer==id_entity)
                )
            )

        #zera o SQL se for admin
        if userType=='A':
            query = Select(func.count(
                    text("DISTINCT id")
                ).label("total"))\
                    .select_from(FprDevolution)\
                    .where(FprDevolution.status.in_([
                        DevolutionStatus.APPROVED_ALL.value,
                        DevolutionStatus.APPROVED_PART.value,
                        DevolutionStatus.PENDING.value
                    ]))
            
        # _show_query(query)

        return db.session.execute(query).one().total if userType!='A' else db.session.execute(query).scalar()

ns_devolution.add_resource(DevolutionTotal,'/indicator/<int:id_entity>')