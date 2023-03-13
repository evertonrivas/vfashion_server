from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmUsers,db
import sqlalchemy as sa
from sqlalchemy import exc
from datetime import datetime
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
        "type": fields.String(enum=['A','L','R','V','U']),
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
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search   = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))

        try:
            if request.args.get("query")!=None:
                rquery = CmmUsers.query.filter(sa.and_(CmmUsers.username.like(search),CmmUsers.active==True)).paginate(page=pag_num,per_page=pag_size)
            else:
                rquery = CmmUsers.query.filter(CmmUsers.active==True).paginate(page=pag_num,per_page=pag_size)

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
                    "type": m.type,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                } for m in rquery.items]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_user.response(HTTPStatus.OK.value,"Cria um novo usuário no sistema")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo usuário!")
    @ns_user.param("username","Login do usuário","formData",required=True)
    @ns_user.param("password","Senha do usuário","formData",required=True)
    @ns_user.param("type","Tipo do usuário","formData",required=True,enum=['A','L','R','V','U'])
    @auth.login_required
    def post(self):
        try:
            usr = CmmUsers()
            usr.username = request.form.get("username")
            usr.type     = request.form.get("type")
            usr.hash_pwd(request.form.get("password"))
            usr.token = ""
            usr.token_expire = datetime.now().utcnow()
            db.session.add(usr)
            db.session.commit()
            return  usr.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


@ns_user.route("/<int:id>")
@ns_user.param("id","Id do registro")
class UserApi(Resource):
    @ns_user.response(HTTPStatus.OK.value,"Obtem um registro de usuario",usr_model)
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def get(self,id:int):
        try:
            return CmmUsers.query.get(id).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_user.response(HTTPStatus.OK.value,"Salva dados de um usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @ns_user.param("username","Nome de login","formData",required=True)
    @ns_user.param("password","Senha do usuário","formData")
    @ns_user.param("type","Tipo do usuário","formData",required=True,enum=['A','L','R','V','U'])
    @auth.login_required
    def post(self,id:int)->bool:
        try:
            usr = CmmUsers.query.get(id)
            usr.username = usr.username if request.form.get("username") is None else request.form.get("username")
            usr.password = usr.password if request.form.get("password") is None else usr.hash_pwd(request.form.get("password"))
            usr.type     = usr.type if request.form.get("type") is None else request.form.get("type")
            usr.active   = usr.active if request.form.get("active") is None else bool(request.form.get("active"))
            db.session.commit()
            return True
        except exc.DatabaseError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_user.response(HTTPStatus.OK.value,"Exclui os dados de um usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def delete(self,id:int)->bool:
        try:
            usr = CmmUsers.query.get(id)
            usr.active = False
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

class UserAuth(Resource):
    @ns_user.response(HTTPStatus.OK.value,"Realiza login e retorna o token")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_user.param("username","Login do sistema","formData",required=True)
    @ns_user.param("password","Senha do sistema","formData",required=True)
    def post(self):
        #req = request.get_json()
        usr = CmmUsers.query.filter(sa.and_(CmmUsers.username==request.form.get("username"),CmmUsers.active==True)).first()
        if usr:
            #verifica a senha criptografada anteriormente
            pwd = request.form.get("password").encode()
            if bcrypt.checkpw(pwd,str(usr.password).encode()):
                obj_retorno = {
					"token_access": usr.get_token(),
					"token_type": "Bearer",
					"token_expire": usr.token_expire.strftime("%Y-%m-%d %H:%M:%S"),
					"level_access": usr.type,
                    "id_user": usr.id
                }
                usr.is_authenticate = True
                db.session.commit()
                return obj_retorno
            else:
                return 0 #senha invalida
        return -1 #usuario invalido

ns_user.add_resource(UserAuth,"/auth")

class UserAuthCheck(Resource):
	def post(self):
		try:
			return False if CmmUsers.check_token(request.form.get("token")) is None else True
		except:
			return False
ns_user.add_resource(UserAuthCheck,"/auth-check")


@ns_user.param("id","Id do registro")
class UserAuthLogout(Resource):
     def post(self,id:int):
        try:
            usr = CmmUsers.query.get(id)
            usr.logout()
            db.session.commit()
            return True
        except:
            return False
        
ns_user.add_resource(UserAuthLogout,"/logout/<int:id>")