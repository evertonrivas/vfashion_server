from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmCities, CmmCountries, CmmLegalEntityContact, CmmStateRegions, CrmFunnelStageCustomer, _get_params,CmmLegalEntities,CmmUserEntity,db
from sqlalchemy import Select,and_,exc,asc,desc,func
from auth import auth
from config import Config

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
        pag_num   =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search    = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params = _get_params(search)

            direction = asc if hasattr(params,'order')==False else asc if params.order=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search = None if hasattr(params,"search")==False else params.search

            rquery = Select(
                    CmmLegalEntities.id,
                    CmmLegalEntities.name.label("social_name"),
                    CmmLegalEntities.fantasy_name,
                    CmmLegalEntities.postal_code,
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
                .order_by(direction(getattr(CmmLegalEntities,order_by)))
            
            if search!=None:
                rquery = rquery.where(
                    CmmCountries.name.like(search) | 
                    CmmStateRegions.name.like(search) |
                    CmmCities.name.like(search) |
                    CmmLegalEntities.name.like(search) |
                    CmmLegalEntities.fantasy_name.like(search))

            if hasattr(params,'list_all')==False:
                pag = db.paginate(rquery,page=pag_num,per_page=pag_size)

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
                                    "id": m.coutry_id,
                                    "name": m.coutry_name
                                }
                            }
                        },
                        "postal_code": m.postal_code,
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

    @ns_legal.response(HTTPStatus.OK.value,"Cria um novo registro de cliente/representante")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar um novo cliente/representante!")
    @ns_legal.param("name","Nome do Cliente/Representante","formData",required=True)
    @ns_legal.param("taxvat","Número do CNPJ ou CPF no Brasil","formData",required=True)
    @ns_legal.param("state_region","Nome ou sigla do Estado","formData",required=True)
    @ns_legal.param("city","Nome da cidade","formData",required=True)
    @ns_legal.param("postal_code","Número do CEP","formData",type=int,required=True)
    @ns_legal.param("neighborhood","Nome do Bairro","formData",required=True)
    @ns_legal.param("phone","Número do telefone","formData",required=True)
    @ns_legal.param("email","Endereço de e-mail","formData",required=True)
    @ns_legal.param("type","Indicativo do tipo de entidade legal",required=True,enum=['C','R','S'])
    @auth.login_required
    def post(self)->int:
        try:
            cst = CmmLegalEntities()
            cst.name         = request.form.get("name")
            cst.taxvat       = request.form.get("taxvat")
            cst.city         = request.form.get("city")
            cst.postal_code  = request.form.get("postal_code")
            cst.neighborhood = request.form.get("neighborhood")
            cst.instagram    = request.form.get("instagram")
            cst.type = request.form.get("type")
            db.session.add(cst)
            db.session.commit()
            return cst.id
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
                retorno = Select(CmmLegalEntities)\
                    .join(CmmUserEntity,CmmLegalEntities.id==CmmUserEntity.id_entity)\
                    .where(CmmUserEntity.id_user==id)
                return db.session.scalar(retorno).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_legal.response(HTTPStatus.OK.value,"Salva dados de um cliente/representante")
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_legal.param("id","Id do registro")
    @ns_legal.param("name","Nome do Cliente/Representante","formData",required=True)
    @ns_legal.param("taxvat","Número do CNPJ ou CPF no Brasil","formData",required=True)
    @ns_legal.param("id_city","Nome da cidade","formData",required=True)
    @ns_legal.param("postal_code","Número do CEP","formData",type=int,required=True)
    @ns_legal.param("neighborhood","Nome do Bairro","formData",required=True)
    @ns_legal.param("type","Indicativo do tipo de entidade legal",required=True,enum=['C','R','S'])
    @auth.login_required
    def post(self,id:int)->bool:
        try:
            cst = CmmLegalEntities.query.get(id)
            cst.name         = cst.name if request.form.get("name") is None else request.form.get("name")
            cst.taxvat       = cst.taxvat if request.form.get("taxvat") is None else request.form.get("taxvat")
            cst.id_city      = 0
            cst.postal_code  = cst.postal_code if request.form.get("postal_code") is None else request.form.get("postal_code")
            cst.neighborhood = cst.neighborhood if request.form.get("neighborhood") is None else request.form.get("neighborhood")
            cst.trash        = cst.trash if request.form.get("trash") is None else request.form.get("trash")
            cst.type         = cst.type if request.form.get("type") is None else request.form.get("type")
            db.session.commit()
            return True
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
    @auth.login_required
    def get(self,id:int):
        pag_num   =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))

        try:
            params = _get_params(request.args.get("query"))

            direction = asc if hasattr(params,'order')==False else asc if params.order=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search = None if hasattr(params,"search")==False else params.search

            print(params)

            rquery = Select(
                CmmLegalEntities.id,
                CmmLegalEntities.name.label("social_name"),
                CmmLegalEntities.fantasy_name,
                CmmLegalEntities.postal_code,
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
                        "postal_code": m.postal_code,
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
            .join(CmmLegalEntities,CmmLegalEntities.id==CmmLegalEntityContact.id_legal_entity)\
            .where(CmmLegalEntities.id==id_customer)
        
        return [{
            "id": c.id,
            "name": c.name,
            "contact_type": c.contact_type,
            "value": c.value,
            "is_whatsapp": c.is_whatsapp, #E = E-mail, P = Phone
            "is_default": c.is_default
        } for c in db.session.execute(stmt)]

ns_legal.add_resource(EntityOfStage,'/by-crm-stage/<int:id>')