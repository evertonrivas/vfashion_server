from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmLegalEntities, CmmUserEntity, CmmUsers, _get_params,db,_save_log
from sqlalchemy import Select, desc, exc, and_, asc, Insert,Update
from auth import auth
from config import Config,CustomerAction

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
        "name":fields.String,
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
        pag_num   =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size  = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query     = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params    = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            trash     = True if hasattr(params,'active')==False else False #foi invertido
            list_all  = False if hasattr(params,'list_all')==False else True

            filter_type   = None if hasattr(params,'type')==False else params.type

            rquery = Select(CmmUsers.id,
                          CmmUsers.username,
                          CmmUsers.type,
                          CmmUsers.date_created,
                          CmmUsers.date_updated,
                          CmmUsers.active
                          ).where(CmmUsers.active==trash)

            if filter_type is not None:
                rquery = rquery.where(CmmUsers.type==filter_type)

            if search is not None:
                rquery = rquery.where(CmmUsers.username.like("%{}%".format(search)))

            rquery.order_by(direction(getattr(CmmUsers, order_by)))

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
                        "username": m.username,
                        "type": m.type,
                        "active": m.active,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                return [{
                    "id": m.id,
                    "username": m.username,
                    "type": m.type,
                    "active": m.active,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                }for m in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_user.response(HTTPStatus.OK.value,"Cria um ou mais novo(s) usuário(s) no sistema")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar!")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()

            db.session.execute(
                Insert(CmmUsers),[{
                    "username": usr["username"],
                    "password": CmmUsers().hash_pwd(usr["password"]),
                    "type": usr["type"]
                }for usr in req]
            )
            db.session.commit()
            return  True
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
        usr = CmmUsers.query.filter(and_(CmmUsers.username==request.form.get("username"),CmmUsers.active==True)).first()
        if usr is not None:

            #tenta buscar um profile
            idProfile = 0
            entity = CmmUserEntity.query.filter(CmmUserEntity.id_user==usr.id).first()
            if entity is not None:
                idProfile = entity.id_entity

            #verifica a senha criptografada anteriormente
            pwd = request.form.get("password").encode()
            if usr.check_pwd(pwd):
                obj_retorno = {
					"token_access": usr.get_token(),
					"token_type": "Bearer",
					"token_expire": usr.token_expire.strftime("%Y-%m-%d %H:%M:%S"),
					"level_access": usr.type,
                    "id_user": usr.id,
                    "id_profile": idProfile
                }
                usr.is_authenticate = True
                db.session.commit()
                if idProfile!=0:
                    _save_log(idProfile,CustomerAction.SYSTEM_ACCESS,'Efetuou login')
                return obj_retorno
            else:
                return 0 #senha invalida
        return -1 #usuario invalido
    
    def put(self):
        try:
            #print(request.get_json())
            req = request.get_json()
            retorno = CmmUsers.check_token(req['token'])
            return False if retorno is None else retorno.token_expire.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return False
    
    def get(self):
        try:
            usr = CmmUsers.query.get(request.args.get("id"))
            usr.token_expire = usr.renew_token()
            db.session.commit()
            return usr.token_expire.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(e)
            return False

ns_user.add_resource(UserAuth,"/auth")

@ns_user.param("id","Id do registro")
class UserAuthLogout(Resource):
     def post(self,id:int):
        try:
            usr = CmmUsers.query.get(id)
            usr.logout()
            db.session.commit()
            entity = CmmUserEntity.query.filter(CmmUserEntity.id_user==id).first()
            if entity is not None:
                _save_log(entity.id,CustomerAction.SYSTEM_ACCESS,'Efetuou logoff')
            return True
        except:
            return False
        
ns_user.add_resource(UserAuthLogout,"/logout/<int:id>")


class UserUpdate(Resource):
    @ns_user.response(HTTPStatus.OK.value,"Cria um ou mais novo(s) usuário(s) no sistema")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar!")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            db.session.execute(Update(CmmUsers),[{
                "id": m["id"],
                "active":m["active"],
                "type": m["type"]
            }for m in req])
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
ns_user.add_resource(UserUpdate,'/massive-change')

@ns_user.hide
class UserNew(Resource):
    def post(self):
        try:
            req = request.get_json()
            db.session.execute(
                Insert(CmmUsers),[{
                    "username": usr["username"],
                    "password": CmmUsers().hash_pwd(usr["password"]),
                    "type": usr["type"]
                }for usr in req])
            db.session.commit()
            return  True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
ns_user.add_resource(UserNew,'/start')