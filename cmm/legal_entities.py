from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmLegalEntities,CmmUserEntity,db
from sqlalchemy import Select,and_,exc
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
class CustomersList(Resource):
    @ns_legal.response(HTTPStatus.OK.value,"Obtem a listagem de clientes/representantes",lgl_return)
    @ns_legal.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_legal.param("page","Número da página de registros","query",type=int,required=True)
    @ns_legal.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_legal.param("query","Texto para busca","query")
    @ns_legal.param("to_export","Se deve exportar","query",type=bool,default=False)
    @auth.login_required
    def get(self):
        pag_num   =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search    = "" if request.args.get("query") is None else "%{}%".format(request.args.get("query"))
        list_all = False if request.args.get("list_all") is None else bool(request.args.get("list_all"))

        try:
            if search!="":
                rquery = CmmLegalEntities.query.filter(and_(CmmLegalEntities.trash == False,CmmLegalEntities.name.like(search)))
            else:
                rquery = CmmLegalEntities.query.filter(CmmLegalEntities.trash == False)

            if list_all==False:
                rquery = rquery.paginate(page=pag_num,per_page=pag_size)
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
                        "taxvat": m.taxvat,
                        "postal_code": m.postal_code,
                        "neighborhood": m.neighborhood,
                        "type": m.type,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in rquery.items]
                }
            else:
                return [{
                        "id": m.id,
                        "name": m.name,
                        "taxvat": m.taxvat,
                        "state_region":m.state_region,
                        "city": m.city,
                        "postal_code": m.postal_code,
                        "neighborhood": m.neighborhood,
                        "type": m.type,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in rquery.all()]
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
    #@auth.login_required
    def post(self)->int:
        try:
            cst = CmmLegalEntities()
            cst.name         = request.form.get("name")
            cst.taxvat       = request.form.get("taxvat")
            cst.state_region = request.form.get("state_region")
            cst.city         = request.form.get("city")
            cst.postal_code  = request.form.get("postal_code")
            cst.neighborhood = request.form.get("neighborhood")
            cst.phone        = request.form.get("phone")
            cst.email        = request.form.get("email")
            cst.instagram    = request.form.get("instagram")
            cst.is_representative = request.form.get("is_representative")
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
class CustomerApi(Resource):

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
    @ns_legal.param("state_region","Nome ou sigla do Estado","formData",required=True)
    @ns_legal.param("city","Nome da cidade","formData",required=True)
    @ns_legal.param("postal_code","Número do CEP","formData",type=int,required=True)
    @ns_legal.param("neighborhood","Nome do Bairro","formData",required=True)
    @ns_legal.param("phone","Número do telefone","formData",required=True)
    @ns_legal.param("email","Endereço de e-mail","formData",required=True)
    @ns_legal.param("type","Indicativo do tipo de entidade legal",required=True,enum=['C','R','S'])
    @ns_legal.param("instagram","Usuário do instagram (sem a url completa)")
    #@auth.login_required
    def post(self,id:int)->bool:
        try:
            cst = CmmLegalEntities.query.get(id)
            cst.name         = cst.name if request.form.get("name") is None else request.form.get("name")
            cst.taxvat       = cst.taxvat if request.form.get("taxvat") is None else request.form.get("taxvat")
            cst.state_region = cst.state_region if request.form.get("state_region") is None else request.form.get("state_region")
            cst.city         = cst.city if request.form.get("city") is None else request.form.get("city")
            cst.postal_code  = cst.postal_code if request.form.get("postal_code") is None else request.form.get("postal_code")
            cst.neighborhood = cst.neighborhood if request.form.get("neighborhood") is None else request.form.get("neighborhood")
            cst.phone        = cst.phone if request.form.get("phone") is None else request.form.get("phone")
            cst.email        = cst.email if request.form.get("email") is None else request.form.get("email")
            cst.trash        = cst.trash if request.form.get("trash") is None else request.form.get("trash")
            cst.type         = cst.type if request.form.get("type") is None else request.form.get("type")
            cst.instagram    = cst.instagram if request.form.get("instagram") is None else request.form.get("instagram")
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
    #@auth.login_required
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
