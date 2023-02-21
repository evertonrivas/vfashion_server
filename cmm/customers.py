from http import HTTPStatus

from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmCustomers,CmmCustomersGroup,CmmCustomerGroupCustomer,db
import sqlalchemy as sa

ns_customer = Namespace("customers",description="Operações para manipular dados de clientes")
ns_group_customer = Namespace("customer-groups",description="Operações para manipular grupos de clientes")

cst_pag_model = ns_customer.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

cst_model = ns_customer.model(
    "Customer",{
        "id": fields.Integer,
        "name": fields.String,
        "taxvat": fields.String,
        "state_region": fields.String,
        "city": fields.String,
        "postal_code": fields.Integer,
        "neighborhood": fields.String,
        "phone": fields.String,
        "email": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
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
    @ns_customer.param("page","Número da página de registros","query",type=int,required=True)
    @ns_customer.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_customer.param("query","Texto para busca","query")
    def get(self):
        pag_num  =  1 if request.args.get("page")!=None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")!=None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")!=None else "{}%".format(request.args.get("query"))

        if request.args.get("query")!=None:
            rquery = CmmCustomers.query.filter(sa.and_(CmmCustomers.trash == False,CmmCustomers.name.like(search))).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmCustomers.query.filter(CmmCustomers.trash == False).paginate(page=pag_num,per_page=pag_size)

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
                "postal_code": m.postal_code,
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
            cst.name         = request.form.get("name")
            cst.taxvat       = request.form.get("taxvat")
            cst.state_region = request.form.get("state_region")
            cst.city         = request.form.get("city")
            cst.postal_code  = request.form.get("postal_code")
            cst.neighborhood = request.form.get("neighborhood")
            cst.phone        = request.form.get("phone")
            cst.email        = request.form.get("email")
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
            cst.name         = request.form.get("name")
            cst.taxvat       = request.form.get("taxvat")
            cst.state_region = request.form.get("state_region")
            cst.city         = request.form.get("city")
            cst.postal_code  = request.form.get("postal_code")
            cst.neighborhood = request.form.get("neighborhood")
            cst.phone        = request.form.get("phone")
            cst.email        = request.form.get("email")
            if request.form.get("trash")!=None:
                cst.trash = request.form.get("trash")
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

cstg_pag_model = ns_group_customer.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Integer
    }
)

cst_id_model = ns_group_customer.model(
    "Customers",{
        "id": fields.Integer
    }
)

cstg_model = ns_group_customer.model(
    "CustomerGroup",{
        "id": fields.Integer,
        "name": fields.String,
        "need_approval": fields.Boolean,
        "customers": fields.List(fields.Nested(cst_id_model))
    }
)

cstg_return = ns_group_customer.model(
    "CustomerGroupReturn",{
        "pagination": fields.Nested(cstg_pag_model),
        "data": fields.List(fields.Nested(cstg_model))
    }
)



@ns_group_customer.route("/")
class UserGroupsList(Resource):
    @ns_group_customer.response(HTTPStatus.OK.value,"Obtem um registro de um grupo de usuarios",cstg_return)
    @ns_group_customer.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_group_customer.param("page","Número da página de registros","query",type=int,required=True)
    @ns_group_customer.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_group_customer.param("query","Texto para busca","query")
    def get(self):
        pag_num =  1 if request.args.get("page")!=None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")!=None else int(request.args.get("pageSize"))

        if request.args.get("query")!=None:
            search = "{}%".format(request.args.get("query"))
            rquery = CmmCustomersGroup.query.filter(sa.and_(CmmCustomersGroup.trash == False,CmmCustomersGroup.name.like(search))).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmCustomersGroup.query.filter(CmmCustomersGroup.trash == False).paginate(page=pag_num,per_page=pag_size)

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
                "need_approval":m.need_approval,
                "customers": self.get_customers(m.id)
            } for m in rquery.items]
        }

    def get_customers(self,id:int):
        rquery = CmmCustomerGroupCustomer.query.filter_by(id_customer = id)
        return [{
            "id": id
        } for m in rquery.items]

    @ns_group_customer.response(HTTPStatus.OK.value,"Cria um novo grupo de usuários no sistema")
    @ns_group_customer.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    def post(self)->int:

        return 0

@ns_group_customer.route("/<int:id>")
@ns_group_customer.param("id","Id do registro")
class UserGroupApi(Resource):
    @ns_group_customer.response(HTTPStatus.OK.value,"Salva dados de um grupo",cstg_model)
    @ns_group_customer.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int):
        cgroup = CmmCustomersGroup.query.get(id)

        return {
            "id": cgroup.id,
            "name": cgroup.name,
            "need_approval": cgroup.need_approval,
            "customers": self.get_customers(id)
        }

    def get_customers(self,id:int):
        rquery = CmmCustomerGroupCustomer.query.filter_by(id_customer = id)
        return [{
            "id": id
        } for m in rquery.items]
    
    @ns_group_customer.response(HTTPStatus.OK.value,"Atualiza os dados de um grupo")
    @ns_group_customer.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        try:
            grp = CmmCustomersGroup.query.get(id)
            grp.name = request.form.get("name")
            grp.need_approval = request.form.get("need_approval")
            if request.form.get("trash")!=None:
                grp.trash = request.form.get("trash")
            db.session.add(grp)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_group_customer.response(HTTPStatus.OK.value,"Exclui os dados de um grupo")
    @ns_group_customer.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        try:
            grp = CmmCustomersGroup.query.get(id)
            grp.trash = True
            db.session.add(grp)
            db.session.commit()
            return True
        except:
            return False