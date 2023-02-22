from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request
from models import CmmCustomers, CmmCustomersGroup, db
import sqlalchemy as sa

ns_customer = Namespace("customers",description="Operações para manipular dados de clientes")
ns_customerg = Namespace("customer-groups",description="Operações para manipular grupos de clientes")

#API Models
cst_pag_model = ns_customer.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

cst_model = ns_customer.model(
    "Customer",{
        "id": fields.Integer,
        "name": fields.String,
        "taxvat": fields.String,
        "state_region": fields.String,
        "city": fields.String,
        "postal_code": fields.String,
        "neighborhood": fields.String,
        "phone": fields.String,
        "email": fields.String
    }
)

cst_return = ns_customer.model(
    "CustomerReturn",{
        "pagination": fields.Nested(cst_pag_model),
        "data": fields.List(fields.Nested(cst_model))
    }
)

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CLIENTES.             #
####################################################################################
@ns_customer.route("/")
class CustomersList(Resource):
    @ns_customer.response(HTTPStatus.OK.value,"Obtem a listagem de clientes",cst_return)
    @ns_customer.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_customer.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_customer.param("pageSize","Número de registros da página (máximo: 200)",type=int,required=True,default=25)
    @ns_customer.param("query","Texto a ser buscado")
    def get(self):
        pag_num  = 1 if request.args.get("page")==None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")==None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")==None else "{}%".format(request.args.get("search")) 

        if search == "":
            rquery = CmmCustomers.query.filter(CmmCustomers.trash==False).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmCustomers.query.filter(sa.and_(CmmCustomers.trash==False),CmmCustomers.name.like(search)).paginate(page=pag_num,per_page=pag_size)
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
                "state_region":m.state_region,
                "city": m.city,
                "postal_code":m.postal_code,
                "neighborhood": m.neighborhood,
                "phone": m.phone,
                "email": m.email,
                "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            } for m in rquery.items]
        }

    @ns_customer.response(HTTPStatus.OK.value,"Cria um novo registro de cliente")
    @ns_customer.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar um novo cliente!")
    def post(self)->int:
        try:
            cst = CmmCustomers()
            cst.name         = request.form.get("name")==None
            cst.taxvat       = request.form.get("taxvat")==None
            cst.state_region = request.form.get("state_region")==None
            cst.city         = request.form.get("city")==None
            cst.postal_code  = request.form.get("postal_code")==None
            cst.neighborhood = request.form.get("neighborhood")==None
            cst.phone        = request.form.get("phone")==None
            cst.email        = request.form.get("email")==None
            db.session.add(cst)
            db.session.commit()
            return cst.id
        except:
            return 0


@ns_customer.route("/<int:id>")
@ns_customer.param("id","Id do registro")
class CustomerApi(Resource):

    @ns_customer.response(HTTPStatus.OK.value,"Obtem um registro de cliente",cst_model)
    @ns_customer.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int):
        return CmmCustomers.query.get(id).to_dict()

    @ns_customer.response(HTTPStatus.OK.value,"Salva dados de um cliente")
    @ns_customer.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        try:
            cst = CmmCustomers.query.get(id)
            cst.name         = cst.name if request.form.get("name")==None else request.form.get("name")
            cst.taxvat       = cst.taxvat if request.form.get("taxvat")==None else request.form.get("taxvat")
            cst.state_region = cst.state_region if request.form.get("state_region")==None else request.form.get("state_region")
            cst.city         = cst.city if request.form.get("city")==None else request.form.get("city")
            cst.postal_code  = cst.postal_code if request.form.get("postal_code")==None else request.form.get("postal_code")
            cst.neighborhood = cst.neighborhood if request.form.get("neighborhood")==None else request.form.get("neighborhood")
            cst.phone        = cst.phone if request.form.get("phone")==None else request.form.get("phone")
            cst.email        = cst.email if request.form.get("email")==None else request.form.get("email")
            db.session.add(cst)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_customer.response(HTTPStatus.OK.value,"Exclui os dados de um cliente")
    @ns_customer.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        try:
            cst = CmmCustomers.query.get(id)
            cst.trash = True
            db.session.add(cst)
            db.session.commit()
            return True
        except:
            return False


####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE CLIENTES.             #
####################################################################################

grp_pag_model = ns_customerg.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

grp_cst_model = ns_customerg.model(
    "Customers",{
        "id":fields.Integer
    }
)

grp_model = ns_customerg.model(
    "CustomerGroup",{
        "id": fields.Integer,
        "name": fields.String,
        "need_approval": fields.Boolean,
        "customers": fields.List(fields.Nested(grp_cst_model))
    }
)

grp_return = ns_customer.model(
    "CustomerGroupReturn",{
        "pagination": fields.Nested(cst_pag_model),
        "data": fields.List(fields.Nested(cst_model))
    }
)

@ns_customerg.route("/")
class UserGroupsApi(Resource):
    @ns_customerg.response(HTTPStatus.OK.value,"Obtem um registro de um grupo de usuarios",grp_return)
    @ns_customerg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_customer.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_customer.param("pageSize","Número de registros da página (máximo: 200)",type=int,required=True,default=25)
    @ns_customer.param("query","Texto a ser buscado")
    def get(self):
        pag_num  = 1 if request.args.get("page")==None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")==None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")==None else "{}%".format(request.args.get("search"))

        if search != "":
            rquery = CmmCustomersGroup.query.filter(sa.and_(CmmCustomersGroup.trash==False,CmmCustomers.name.like(search))).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmCustomers.query.filter(CmmCustomersGroup.trash==False).paginate(page=pag_num,per_page=pag_size)

        return [{
            "id": m.id,
            "name": m.name,
            "need_approval":m.need_approval,
            "customers":self.get_customers(m.id)
        }for m in rquery.items]

    def get_customers(self,id:int):
        rquery = CmmCustomers.query.find(CmmCustomers.id==id)
        return [{
            "id":m.id
        } for m in rquery.items]


    @ns_customerg.response(HTTPStatus.OK.value,"Cria um novo grupo de clientes no sistema")
    @ns_customerg.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    def post(self)->int:

        return 0


@ns_customerg.route("/<int:id>")
@ns_customerg.param("id","Id do registro")
class UserGroupApi(Resource):
    @ns_customerg.response(HTTPStatus.OK.value,"Salva dados de um grupo",grp_model)
    @ns_customerg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int):
        return CmmCustomersGroup.query.get(id).to_dict()
    
    @ns_customerg.response(HTTPStatus.OK.value,"Salva dados de um grupo")
    @ns_customerg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,_id:int)->bool:
        try:
            grp = CmmCustomersGroup.query.get(id)
            grp.name          = grp.name if request.form.get("name")==None else request.form.get("name")
            grp.need_approval = grp.need_approval if request.form.get("need_approval")==None else request.form.get("need_approval")
            db.session.add(grp)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_customerg.response(HTTPStatus.OK.value,"Exclui os dados de um grupo")
    @ns_customerg.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,_id:int)->bool:
        try:
            grp = CmmCustomersGroup.query.get(id)
            grp.trash = True
            db.session.add(grp)
            db.session.commit()
            return True
        except:
            return False