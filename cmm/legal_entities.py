from datetime import datetime
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import  B2bCustomerGroup, CmmLegalEntityHistory, CmmUsers, _show_query, db,_save_log,_get_params,B2bCustomerGroupCustomers, CmmCities, CmmCountries, CmmLegalEntityContact, CmmLegalEntityFile, CmmStateRegions, CrmFunnelStageCustomer,CmmLegalEntities,CmmUserEntity
from sqlalchemy import Delete, Select, Update,and_,exc,asc,desc,func, or_
from auth import auth
from f2bconfig import CustomerAction
from os import environ

ns_legal = Namespace("legal-entities",description="Operações para manipular dados de clientes/representantes")

lgl_pag_model = ns_legal.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

lgl_registry = ns_legal.model(
    "LegalEntityInsert",{
        "id":fields.Integer,
        "name":fields.String,
        "fantasy_name":fields.String,
        "id_city": fields.Integer,
        "taxvat": fields.String,
        "address": fields.String,
        "postal_code": fields.String,
        "neighborhood": fields.String,
        "type": fields.String
    }
)

lgl_model = ns_legal.model(
    "LegalEntity",{
        "id": fields.Integer,
        "name": fields.String,
        "taxvat": fields.String,
        "postal_code": fields.Integer,
        "neighborhood": fields.String,
        "type": fields.String(enum=['C','R','S']),
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

lgl_return = ns_legal.model(
    "LegalEntitiesReturn",{
        "pagination": fields.Nested(lgl_pag_model),
        "data": fields.List(fields.Nested(lgl_model))
    }
)

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CLIENTES.             #
####################################################################################
@ns_legal.route("/")
class EntitysList(Resource):
    @ns_legal.response(HTTPStatus.OK.value,"Obtem a listagem de clientes/representantes",lgl_return)
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_legal.param("page","Número da página de registros","query",type=int,required=True)
    @ns_legal.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_legal.param("query","Texto para busca","query")
    @ns_legal.param("list_all","Se deve exportar","query",type=bool,default=False)
    @auth.login_required
    def get(self):
        pag_num   = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search    = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params = _get_params(search)

            direction = asc if hasattr(params,'order')==False else asc if params.order=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            trash     = False if hasattr(params,"trash")==False else True
            list_all  = False if hasattr(params,"list_all")==False else True

            filter_search = None if hasattr(params,"search")==False else params.search
            filter_type   = None if hasattr(params,'type')==False else params.type
            filter_rep    = None if hasattr(params,'representative')==False else params.filter_rep
            filter_country = None if hasattr(params,'id_country')==False else params.id_country
            filter_city    = None if hasattr(params,"id_city")==False else params.id_city
            filter_state_region = None if hasattr(params,'id_state_region')==False else params.id_state_region

            rquery = Select(
                    CmmLegalEntities.id,
                    CmmLegalEntities.name.label("social_name"),
                    CmmLegalEntities.fantasy_name,
                    CmmLegalEntities.postal_code,
                    CmmLegalEntities.neighborhood,
                    CmmLegalEntities.address,
                    CmmLegalEntities.taxvat,
                    CmmLegalEntities.type,
                    CmmLegalEntities.date_created,
                    CmmLegalEntities.date_updated,
                    CmmCities.id.label("city_id"),
                    CmmCities.name.label("city_name"),
                    CmmCities.brazil_ibge_code,
                    CmmStateRegions.id.label("state_id"),
                    CmmStateRegions.name.label("state_name"),
                    CmmStateRegions.acronym,
                    CmmCountries.id.label("country_id"),
                    CmmCountries.name.label("country_name"))\
                .join(CmmCities,CmmCities.id==CmmLegalEntities.id_city)\
                .join(CmmStateRegions,CmmStateRegions.id==CmmCities.id_state_region)\
                .join(CmmCountries,CmmCountries.id==CmmStateRegions.id_country)\
                .where(CmmLegalEntities.trash==trash)\
                .order_by(direction(getattr(CmmLegalEntities,order_by)))
            
            if filter_search!=None:
                rquery = rquery.where(
                    or_(
                        CmmCountries.name.like("%{}%".format(filter_search)),
                        CmmStateRegions.name.like("%{}%".format(filter_search)),
                        CmmCities.name.like("%{}%".format(filter_search)),
                        CmmLegalEntities.name.like("%{}%".format(filter_search)),
                        CmmLegalEntities.fantasy_name.like("%{}%".format(filter_search)),
                        CmmLegalEntities.address.like("%{}%".format(filter_search)),
                        CmmLegalEntities.neighborhood.like("%{}%".format(filter_search)),
                        CmmLegalEntities.taxvat.like("%{}%".format(filter_search))
                    )
                )
                
            if filter_rep is not None:
                rquery = rquery.where(CmmLegalEntities.id.in_(
                    Select(B2bCustomerGroupCustomers.id_customer).where(B2bCustomerGroupCustomers.id_representative==filter_rep)
                ))
                
            if filter_type is not None:
                rquery = rquery.where(CmmLegalEntities.type==filter_type)

            if filter_city is not None:
                rquery = rquery.where(CmmCities.id==filter_city)

            if filter_state_region is not None:
                rquery = rquery.where(CmmStateRegions.id==filter_state_region)

            if filter_country is not None:
                rquery = rquery.where(CmmCountries.id==filter_country)

            if list_all==False:
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
                        "name": m.social_name,
                        "fantasy_name": m.fantasy_name,
                        "taxvat": m.taxvat,
                        "city": {
                            "id": m.city_id,
                            "name": m.city_name,
                            "stage_region": {
                                "id": m.state_id,
                                "name": m.state_name,
                                "acronym": m.acronym,
                                "country":{
                                    "id": m.country_id,
                                    "name": m.country_name
                                }
                            }
                        },
                        "postal_code": m.postal_code,
                        "address": m.address,
                        "neighborhood": m.neighborhood,
                        "type": m.type,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                return [{
                        "id": m.id,
                        "name": m.social_name,
                        "fantasy_name": m.fantasy_name,
                        "taxvat": m.taxvat,
                        "city": {
                            "id": m.city_id,
                            "name": m.city_name,
                            "stage_region": {
                                "id": m.state_id,
                                "name": m.state_name,
                                "acronym": m.acronym,
                                "country":{
                                    "id": m.country_id,
                                    "name": m.country_name
                                }
                            }
                        },
                        "postal_code": m.postal_code,
                        "address": m.address,
                        "neighborhood": m.neighborhood,
                        "type": m.type,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery).all()]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        except Exception as e:
            return  {
                "error_code": 0,
                "error_details": e.args,
                "error_sql": ""
            }        

    @ns_legal.response(HTTPStatus.OK.value,"Cria um novo registro de cliente/representante/fornecedor",model=lgl_registry)
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar um novo cliente/representante/fornecedor!")
    @auth.login_required
    def post(self)->int:
        try:
            req = request.get_json()
            cst = CmmLegalEntities()
            cst.name         = req["name"]
            cst.fantasy_name = req["fantasy_name"]
            cst.id_city      = req["city"]["id"]
            cst.taxvat       = req["taxvat"]
            cst.address      = req["address"]
            cst.postal_code  = req["postal_code"]
            cst.neighborhood = req["neighborhood"]
            cst.type         = req["type"]
            cst.trash        = False
            cst.activation_date = datetime.now()
            db.session.add(cst)
            db.session.commit()

            if req["agent"] is not None:
                grp = db.session.execute(Select(B2bCustomerGroup.id).where(B2bCustomerGroup.id_representative==req["agent"])).first()
                if grp is not None:
                    grpc = B2bCustomerGroupCustomers()
                    grpc.id_customer_group = grp.id
                    grpc.id_customer = cst.id
                    db.session.add(grpc)
                    db.session.commit()

            for contact in req["contacts"]:
                ct                 = CmmLegalEntityContact()
                ct.id_legal_entity = cst.id
                ct.name            = contact["name"]
                ct.contact_type    = contact["contact_type"]
                ct.value           = contact["value"]
                ct.is_default      = contact["is_default"]
                ct.is_whatsapp     = contact["is_whatsapp"]
                db.session.add(ct)

            db.session.commit()

            _save_log(cst.id,CustomerAction.DATA_REGISTERED,'Registro criado')

            return cst.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_legal.response(HTTPStatus.OK.value,"Exclui os dados de um cliente/representante")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self)->bool:
        try:
            req = request.get_json()
            for id in req["ids"]:
                # move a(s) entidade(s) para a lixeira
                cst = CmmLegalEntities.query.get(id)
                cst.trash = req["toTrash"]
                db.session.commit()

                for usr in db.session.execute(Select(CmmUserEntity).where(CmmUserEntity.id_entity==id)):
                    db.session.execute(
                        Update(CmmUsers).values(active=(False if req["toTrash"]==1 else True)).where(CmmUsers.id==usr)
                    )
                    db.session.commit()

                _save_log(id,CustomerAction.DATA_DELETED,'Registro e usuários '+('movido para a' if req["toTrash"]==1 else 'removido da') +' Lixeira')
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


@ns_legal.route("/<int:id>")
class EntityApi(Resource):

    @ns_legal.response(HTTPStatus.OK.value,"Obtem um registro de cliente",lgl_model)
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_legal.param("id","Id do usuário do sistema (tabela CmmUser)")
    @auth.login_required
    def get(self,id:int):
        try:
            rquery = Select(
                CmmLegalEntities.id,
                CmmLegalEntities.origin_id,
                CmmLegalEntities.name.label("social_name"),
                CmmLegalEntities.fantasy_name,
                CmmLegalEntities.postal_code,
                CmmLegalEntities.address,
                CmmLegalEntities.neighborhood,
                CmmLegalEntities.taxvat,
                CmmLegalEntities.type,
                CmmLegalEntities.date_created,
                CmmLegalEntities.date_updated,
                CmmCities.id.label("city_id"),
                CmmCities.name.label("city_name"),
                CmmCities.brazil_ibge_code,
                CmmStateRegions.id.label("state_id"),
                CmmStateRegions.name.label("state_name"),
                CmmStateRegions.acronym,
                CmmCountries.id.label("country_id"),
                CmmCountries.name.label("country_name"))\
            .join(CmmCities,CmmCities.id==CmmLegalEntities.id_city)\
            .join(CmmStateRegions,CmmStateRegions.id==CmmCities.id_state_region)\
            .join(CmmCountries,CmmCountries.id==CmmStateRegions.id_country)\
            .where(CmmLegalEntities.id==id)

            m = db.session.execute(rquery).first()

            return {
                    "id": m.id,
                    "origin_id": m.origin_id,
                    "name": m.social_name,
                    "fantasy_name": m.fantasy_name,
                    "taxvat": m.taxvat,
                    "city": {
                        "id": m.city_id,
                        "name": m.city_name,
                        "brazil_ibge_code":m.brazil_ibge_code,
                        "state_region": {
                            "id": m.state_id,
                            "name": m.state_name,
                            "acronym": m.acronym,
                            "country":{
                                "id": m.country_id,
                                "name": m.country_name
                            }
                        }
                    },
                    "agent": self.__get_representative(m.id),
                    "contacts": self.__get_contacts(m.id),
                    "files": self.__get_file(m.id),
                    "postal_code": m.postal_code,
                    "neighborhood": m.neighborhood,
                    "address": m.address,
                    "type": m.type,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None,
                }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    def __get_contacts(self,id_customer:int):
        stmt = Select(CmmLegalEntityContact.id,
                      CmmLegalEntityContact.name,
                      CmmLegalEntityContact.contact_type,
                      CmmLegalEntityContact.value,
                      CmmLegalEntityContact.is_whatsapp,
                      CmmLegalEntityContact.is_default)\
            .where(CmmLegalEntityContact.id_legal_entity==id_customer)
        
        return [{
            "id": c.id,
            "id_legal_entity": id_customer,
            "name": c.name,
            "contact_type": c.contact_type,
            "value": c.value,
            "is_whatsapp": c.is_whatsapp, #E = E-mail, P = Phone
            "is_default": c.is_default
        } for c in db.session.execute(stmt)]
    
    def __get_file(self,id_customer:int):
        stmt = Select(CmmLegalEntityFile.id,
                      CmmLegalEntityFile.name,
                      CmmLegalEntityFile.folder,
                      CmmLegalEntityFile.content_type
                      ).where(CmmLegalEntityFile.id_legal_entity==id_customer)
        return [{
            "id": c.id,
            "name": c.name,
            "folder": c.folder,
            "content_type":c.content_type
        }for c in db.session.execute(stmt)]
    
    def __get_representative(self,id:int):
        try:
            rquery = Select(
                    CmmLegalEntities.id,
                    CmmLegalEntities.origin_id,
                    CmmLegalEntities.name.label("social_name"),
                    CmmLegalEntities.fantasy_name,
                    CmmLegalEntities.postal_code,
                    CmmLegalEntities.neighborhood,
                    CmmLegalEntities.address,
                    CmmLegalEntities.taxvat,
                    CmmLegalEntities.type,
                    CmmLegalEntities.date_created,
                    CmmLegalEntities.date_updated,
                    CmmCities.id.label("city_id"),
                    CmmCities.name.label("city_name"),
                    CmmCities.brazil_ibge_code,
                    CmmStateRegions.id.label("state_id"),
                    CmmStateRegions.name.label("state_name"),
                    CmmStateRegions.acronym,
                    CmmCountries.id.label("country_id"),
                    CmmCountries.name.label("country_name"))\
                .join(CmmCities,CmmCities.id==CmmLegalEntities.id_city)\
                .join(CmmStateRegions,CmmStateRegions.id==CmmCities.id_state_region)\
                .join(CmmCountries,CmmCountries.id==CmmStateRegions.id_country)\
                .join(B2bCustomerGroupCustomers,B2bCustomerGroupCustomers.id_representative==CmmLegalEntities.id)\
                .where(and_(CmmLegalEntities.trash==False,B2bCustomerGroupCustomers.id_customer==id))
            
            m = db.session.execute(rquery).first()

            return {
                    "id": m.id,
                    "origin_id": m.origin_id,
                    "name": m.social_name,
                    "fantasy_name": m.fantasy_name,
                    "taxvat": m.taxvat,
                    "city": {
                        "id": m.city_id,
                        "name": m.city_name,
                        "brazil_ibge_code":m.brazil_ibge_code,
                        "state_region": {
                            "id": m.state_id,
                            "name": m.state_name,
                            "acronym": m.acronym,
                            "country":{
                                "id": m.country_id,
                                "name": m.country_name
                            }
                        }
                    },
                    "contacts": self.__get_contacts(m.id),
                    "web": self.__get_web(m.id),
                    "files": self.__get_file(m.id),
                    "postal_code": m.postal_code,
                    "neighborhood": m.neighborhood,
                    "address": m.address,
                    "type": m.type,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                }
        except:
            return None

    @ns_legal.response(HTTPStatus.OK.value,"Salva dados de um cliente/representante/fornecedor",model=lgl_registry)
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int)->bool:
        try:
            req = request.get_json()
            cst:CmmLegalEntities = CmmLegalEntities.query.get(id)
            cst.name         = req["name"]
            cst.fantasy_name = req["fantasy_name"]
            cst.id_city      = req["city"]["id"]
            cst.taxvat       = req["taxvat"]
            cst.address      = req["address"]
            cst.postal_code  = req["postal_code"]
            cst.neighborhood = req["neighborhood"]
            cst.type         = req["type"]
            cst.date_updated = datetime.now()
            db.session.commit()

            #limpa o que existe no grupo para nao gerar duplicacao de chave
            db.session.execute(Delete(B2bCustomerGroupCustomers).where(B2bCustomerGroupCustomers.id_customer==id))
            db.session.commit()

            if req["agent"] is not None:
                grp = db.session.execute(Select(B2bCustomerGroup.id).where(B2bCustomerGroup.id_representative==req["agent"])).first()
                if grp is not None:
                    grpc = B2bCustomerGroupCustomers()
                    grpc.id_customer_group = grp.id
                    grpc.id_customer = cst.id
                    db.session.add(grpc)
                    db.session.commit()

            for contact in req["contacts"]:
                if contact["id"] == 0:
                    ct                 = CmmLegalEntityContact()
                    ct.id_legal_entity = cst.id
                    ct.name            = contact["name"]
                    ct.contact_type    = contact["contact_type"]
                    ct.value           = contact["value"]
                    ct.is_default      = contact["is_default"]
                    ct.is_whatsapp     = contact["is_whatsapp"]
                    db.session.add(ct)
                    db.session.commit()
                else:
                    ct              = CmmLegalEntityContact.query.get(contact["id"])
                    ct.name         = contact["name"]
                    ct.contact_type = contact["contact_type"]
                    ct.value        = contact["value"]
                    ct.is_default   = contact["is_default"]
                    ct.is_whatsapp  = contact["is_whatsapp"]
                    db.session.commit()
            
            _save_log(id,CustomerAction.DATA_UPDATED,'Registro alterado')

            return id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_legal.response(HTTPStatus.OK.value,"Exclui os dados de um cliente/representante")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_legal.param("id","Id do registro")
    @auth.login_required
    def delete(self,id:int)->bool:
        try:
            cst = CmmLegalEntities.query.get(id)
            cst.trash = True
            db.session.commit()
            _save_log(id,CustomerAction.DATA_DELETED,'Registro arquivado')
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

class EntityCount(Resource):
    @ns_legal.response(HTTPStatus.OK.value,"Retorna o total de Entidades por tipo")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_legal.param("type","Tipo da Entidade","query",type=str,enum=['C','R','S'])
    @auth.login_required
    def get(self):
        try:
            stmt = Select(func.count(CmmLegalEntities.id).label("total")).select_from(CmmLegalEntities).where(CmmLegalEntities.type==request.args.get("type"))
            return db.session.execute(stmt).first().total
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
ns_legal.add_resource(EntityCount,'/count')

class EntityOfStage(Resource):
    @ns_legal.response(HTTPStatus.OK.value,"Retorna o total de Entidades por tipo")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_legal.param("page","Número da página de registros","query",type=int,required=True)
    @ns_legal.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_legal.param("query","Número de registros por página","query",type=str)
    @auth.login_required
    def get(self,id:int):
        pag_num   = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))

        try:
            params = _get_params(request.args.get("query"))

            direction = asc if hasattr(params,'order')==False else asc if params.order=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search = None if hasattr(params,"search")==False else params.search

            rquery = Select(
                CmmLegalEntities.id,
                CmmLegalEntities.name.label("social_name"),
                CmmLegalEntities.fantasy_name,
                CmmLegalEntities.postal_code,
                CmmLegalEntities.address,
                CmmLegalEntities.neighborhood,
                CmmLegalEntities.taxvat,
                CmmLegalEntities.type,
                CmmLegalEntities.date_created,
                CmmLegalEntities.date_updated,
                CmmCities.id.label("city_id"),
                CmmCities.name.label("city_name"),
                CmmCities.brazil_ibge_code,
                CmmStateRegions.id.label("state_id"),
                CmmStateRegions.name.label("state_name"),
                CmmStateRegions.acronym,
                CmmCountries.id.label("country_id"),
                CmmCountries.name.label("country_name"))\
            .join(CmmCities,CmmCities.id==CmmLegalEntities.id_city)\
            .join(CmmStateRegions,CmmStateRegions.id==CmmCities.id_state_region)\
            .join(CmmCountries,CmmCountries.id==CmmStateRegions.id_country)\
            .join(CrmFunnelStageCustomer,CrmFunnelStageCustomer.id_customer==CmmLegalEntities.id)\
            .where(CrmFunnelStageCustomer.id_funnel_stage==id)\
            .order_by(direction(getattr(CmmLegalEntities,order_by)))

            #_show_query(rquery)

            if search!=None:
                rquery = rquery.where(
                    CmmCountries.name.like(search) | 
                    CmmStateRegions.name.like(search) |
                    CmmCities.name.like(search) |
                    CmmLegalEntities.name.like(search) |
                    CmmLegalEntities.fantasy_name.like(search) | 
                    CmmLegalEntities.neighborhood.like(search)
                )
                
            pag = db.paginate(rquery,page=pag_num,per_page=pag_size)

            rquery = rquery.limit(pag_size).offset((pag_num - 1) * pag_size)

            return {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next,
                    },
                    "data":[{
                        "id": m.id,
                        "name": m.social_name,
                        "fantasy_name": m.fantasy_name,
                        "taxvat": m.taxvat,
                        "city": {
                            "id": m.city_id,
                            "name": m.city_name,
                            "brazil_ibge_code":m.brazil_ibge_code,
                            "state_region": {
                                "id": m.state_id,
                                "name": m.state_name,
                                "acronym": m.acronym,
                                "country":{
                                    "id": m.country_id,
                                    "name": m.country_name
                                }
                            }
                        },
                        "contacts": self.__get_contacts(m.id),
                        "files": self.__get_file(m.id),
                        "postal_code": m.postal_code,
                        "address": m.address,
                        "neighborhood": m.neighborhood,
                        "type": m.type,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    def __get_contacts(self,id_customer:int):
        stmt = Select(CmmLegalEntityContact.id,
                      CmmLegalEntityContact.name,
                      CmmLegalEntityContact.contact_type,
                      CmmLegalEntityContact.value,
                      CmmLegalEntityContact.is_whatsapp,
                      CmmLegalEntityContact.is_default)\
            .where(CmmLegalEntityContact.id_legal_entity==id_customer)
        
        return [{
            "id": c.id,
            "id_legal_entity": id_customer,
            "name": c.name,
            "contact_type": c.contact_type,
            "value": c.value,
            "is_whatsapp": c.is_whatsapp, #E = E-mail, P = Phone
            "is_default": c.is_default
        } for c in db.session.execute(stmt)]
    
    def __get_file(self,id_customer:int):
        stmt = Select(CmmLegalEntityFile.id,
                      CmmLegalEntityFile.name,
                      CmmLegalEntityFile.folder,
                      CmmLegalEntityFile.content_type
                      ).where(CmmLegalEntityFile.id_legal_entity==id_customer)
        return [{
            "id": c.id,
            "name": c.name,
            "folder": c.folder,
            "content_type":c.content_type
        }for c in db.session.execute(stmt)]

    @ns_legal.response(HTTPStatus.OK.value,"Adiciona um ou mais clientes em um estagio de um funil")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Falha ao adicionar cliente!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            for entity in req["entities"]:
                #verifica se ja ha registro
                exist = db.session.execute(
                    Select(func.count().label("total")).select_from(CrmFunnelStageCustomer).where(
                        and_(
                            CrmFunnelStageCustomer.id_customer==entity["id"],
                            CrmFunnelStageCustomer.id_funnel_stage==id
                        )
                    )
                ).first().total

                if exist == 0:
                    crm = CrmFunnelStageCustomer()
                    crm.id_customer = entity["id"]
                    crm.id_funnel_stage = id
                    db.session.add(crm)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
ns_legal.add_resource(EntityOfStage,'/by-crm-stage/<int:id>')

class EntityContact(Resource):
    @ns_legal.response(HTTPStatus.OK.value,"Salva contato(s) de uma entidade")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Falha ao salvar o(s) registro(s)!")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            #print(req)
            for r in req:
                ct = CmmLegalEntityContact()
                ct.id              = r['id']
                ct.id_legal_entity = r['id_legal_entity']
                ct.name            = r['name']
                ct.contact_type    = r['contact_type']
                ct.is_default      = r['is_default']
                ct.is_whatsapp     = r['is_whatsapp']
                ct.value           = r['value']
                if ct.id == 0:
                    _save_log(r['id_legal_entity'],CustomerAction.DATA_REGISTERED,'Adicionado contato '+r['name'])
                    db.session.add(ct)
                else:
                    _save_log(r['id_legal_entity'],CustomerAction.DATA_UPDATED,'Atualizado contato '+r['name'])
                db.session.commit()
                return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_legal.response(HTTPStatus.OK.value,"Exclui contato(s) de uma entidade")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            pass
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
ns_legal.add_resource(EntityContact,'/save-contacts')

class EntityHistory(Resource):
    @ns_legal.response(HTTPStatus.OK.value,"Obtem os dados históricos de uma entidade")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_legal.param("page","Número da página de registros","query",type=int,required=True)
    @ns_legal.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_legal.param("query","Texto para busca","query")
    @auth.login_required
    def get(self,id:int):
        pag_num   = 1 if request.args.get("page") is None or request.args.get("page")==0 else int(request.args.get("page"))
        pag_size  = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search    = "" if request.args.get("query") is None else request.args.get("query")
        try:
            params = _get_params(search)

            rquery = Select(CmmLegalEntityHistory.id,
                            CmmLegalEntityHistory.id_legal_entity,
                            CmmLegalEntityHistory.history,
                            CmmLegalEntityHistory.action,
                            CmmLegalEntityHistory.date_created)\
                            .where(CmmLegalEntityHistory.id_legal_entity==id)
            
            if hasattr(params,'search'):
                rquery = rquery.where(CmmLegalEntityHistory.history.like('%{}%'.format(params.search)))
            

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
                        "id": r.id,
                        "id_legal_entity": r.id_legal_entity,
                        "history": r.history,
                        "action": r.action,
                        "date_created": r.date_created.strftime("%d/%m/%Y %H:%M:%S")
                    }for r in db.session.execute(rquery)]
            }
            
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
ns_legal.add_resource(EntityHistory,'/load-history/<int:id>')


class EntityImport(Resource):
    @ns_legal.response(HTTPStatus.OK.value,"Realiza o pocessamento dos registros do arquivo de importacao")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Falha ao processar registros")
    def post(self):
        try:
            pass
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }