from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmUsers,db
import sqlalchemy as sa

ns_user = Namespace("users",description="Operações para manipular dados de usuários do sistema")

usr_pag_mode = ns_user.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

usr_model = ns_user.model(
    "User",{
        "id": fields.Integer,
        "username": fields.String,
        "password": fields.String,
        "name": fields.String,
        "type": fields.String,
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

usr_return = ns_user.model(
    "UserReturn",{
        "pagination": fields.Nested(usr_pag_mode),
        "data": fields.List(fields.Nested(usr_model))
    }
)

@ns_user.route("/")
class UsersList(Resource):

    @ns_user.response(HTTPStatus.OK.value,"Obtem a listagem de usuários",usr_return)
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha oa listar registros!")
    @ns_user.param("page","Número da página de registros","query",type=int,required=True)
    @ns_user.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_user.param("query","Texto para busca","query")
    def get(self):
        pag_num  =  1 if request.args.get("page")!=None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize")!=None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query")!=None else "{}%".format(request.args.get("query"))

        if request.args.get("query")!=None:
            rquery = CmmUsers.query.filter(sa.and_(CmmUsers.name.like(search),CmmUsers.active==False)).paginate(page=pag_num,per_page=pag_size)
        else:
            rquery = CmmUsers.query.filter(CmmUsers.active==False).paginate(page=pag_num,per_page=pag_size)

        #pedro maria
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
                "username": m.username,
                "password": m.password,
                "name": m.name,
                "type": m.type,
                "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            } for m in rquery.items]
        }

    @ns_user.response(HTTPStatus.OK.value,"Cria um novo usuário no sistema")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo usuário!")
    @ns_user.param("name","Nome da pessoa","formData",required=True)
    @ns_user.param("username","Login do usuário","formData",required=True)
    @ns_user.param("password","Senha do usuário","formData",required=True)
    @ns_user.param("type","Tipo do usuário","formData",required=True)
    def post(self)->int:
        try:
            usr = CmmUsers()
            usr.name     = request.form.get("name")
            usr.username = request.form.get("username")
            usr.password = request.form.get("password")
            usr.type     = request.form.get("type")
            db.session.add(usr)
            db.session.commit()
            return usr.id
        except:
            return 0


@ns_user.route("/<int:id>")
@ns_user.param("id","Id do registro")
class UserApi(Resource):
    @ns_user.response(HTTPStatus.OK.value,"Obtem um registro de usuario",usr_model)
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int):
        return CmmUsers.query.get(id).to_dict()

    @ns_user.response(HTTPStatus.OK.value,"Salva dados de um usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_user.param("name","Nome do usuário","formData",required=True)
    @ns_user.param("username","Nome de login","formData",required=True)
    @ns_user.param("password","Senha do usuário","formData",required=True)
    @ns_user.param("type","Tipo do usuário","formData",required=True)
    def post(self,id:int)->bool:
        try:
            usr = CmmUsers.query.get(id)
            usr.name     = request.form.get("name")
            usr.username = request.form.get("username")
            usr.password = request.form.get("password")
            usr.type     = request.form.get("type")
            db.session.add(usr)
            db.session.commit()
            return True
        except:
            return False
    
    @ns_user.response(HTTPStatus.OK.value,"Exclui os dados de um usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        try:
            usr = CmmUsers.query.get(id)
            usr.active = False
            db.session.add(usr)
            db.session.commit()
            return True
        except:
            return False