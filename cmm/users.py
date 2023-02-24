from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmUsers,db
import sqlalchemy as sa
import bcrypt
from auth import auth

ns_user = Namespace("users",description="Operações para manipular dados de usuários do sistema")

#API Models
usr_pag_model = ns_user.model(
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
        "type": fields.String(enum=['A','L','R','V']),
        "date_created": fields.DateTime,
        "date_updated": fields.DateTime
    }
)

usr_return = ns_user.model(
    "UserReturn",{
        "pagination": fields.Nested(usr_pag_model),
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
    #@auth.login_required
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
                "type": m.type,
                "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S")
            } for m in rquery.items]
        }

    @ns_user.response(HTTPStatus.OK.value,"Cria um novo usuário no sistema")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo usuário!")
    @ns_user.param("username","Login do usuário","formData",required=True)
    @ns_user.param("password","Senha do usuário","formData",required=True)
    @ns_user.param("type","Tipo do usuário","formData",required=True)
    #@auth.login_required
    def post(self)->int:
        try:
            usr = CmmUsers()
            usr.username = usr.username if request.form.get("username") is None else request.form.get("username")
            usr.password = usr.password if request.form.get("password") is None else bcrypt.hashpw(request.form.get("password"),bcrypt.gensalt())
            usr.type     = usr.type if request.form.get("type") is None else request.form.get("type")
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
    #@auth.login_required
    def get(self,id:int):
        return CmmUsers.query.get(id).to_dict()

    @ns_user.response(HTTPStatus.OK.value,"Salva dados de um usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_user.param("username","Nome de login","formData",required=True)
    @ns_user.param("password","Senha do usuário","formData",required=True)
    @ns_user.param("type","Tipo do usuário","formData",required=True)
    #@auth.login_required
    def post(self,id:int)->bool:
        try:
            usr = CmmUsers.query.get(id)
            usr.username = usr.username if request.form.get("username")==None else request.form.get("username")
            usr.password = usr.password if request.form.get("password")==None else request.form.get("password")
            usr.type     = usr.type if request.form.get("type")==None else request.form.get("type")
            usr.active   = usr.active if request.form.get("active")==None else request.form.get("active")
            db.session.commit()
            return True
        except:
            return False
    
    @ns_user.response(HTTPStatus.OK.value,"Exclui os dados de um usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    #@auth.login_required
    def delete(self,id:int)->bool:
        try:
            usr = CmmUsers.query.get(id)
            usr.active = False
            db.session.commit()
            return True
        except:
            return False

class UserAuth(Resource):
    @ns_user.response(HTTPStatus.OK.value,"Realiza login e retorna o token")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_user.param("username","Login do sistema","formData",required=True)
    @ns_user.param("password","Senha do sistema","formData",required=True)
    def post(username:str,password:str):
        usr = CmmUsers.query.filter(sa.and_(CmmUsers.username==username,CmmUsers.active==True)).first()
        if usr:
            #verifica a senha criptografada anteriormente
            if bcrypt.checkpw(password,usr.password):
                return {
                    "token": usr.get_token(),
                    "user": {
                        "type": usr.type,
                        "name": usr.name
                    }
                }
            else:
                return 0 #senha invalida
        return 0 #usuario invalido


ns_user.add_resource(UserAuth,"/auth")