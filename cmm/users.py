from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from datetime import datetime
from models.helpers import db
from common import _send_email
# from models import _show_query
from flask_restx import Resource,Namespace,fields
from f2bconfig import ContactType,CustomerAction, MailTemplates
from models.tenant import CmmLegalEntities, CmmLegalEntityContact
from models.tenant import CmmUserEntity, _get_params, _save_log
from models.public import SysUsers
from sqlalchemy import Delete, Select, desc, exc, and_, asc, Insert, func, or_

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
        pag_num   = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size  = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query     = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params    = _get_params(query)
            if params is not None:
                direction = asc if not hasattr(params,'order') else asc if str(params.order).upper()=='ASC' else desc
                order_by  = 'id' if not hasattr(params,'order_by') else params.order_by
                search    = None if not hasattr(params,"search") else params.search
                trash     = True if not hasattr(params,'active') else False if params.active=="1" else True #foi invertido
                list_all  = False if not hasattr(params,'list_all') else True
                filter_type   = None if not hasattr(params,'type') else params.type

            rquery = Select(SysUsers.id,
                          SysUsers.username,
                          SysUsers.type,
                          SysUsers.date_created,
                          SysUsers.date_updated,
                          SysUsers.active
                          ).where(SysUsers.active==trash)\
                          .order_by(direction(getattr(SysUsers, order_by)))

            if filter_type is not None:
                rquery = rquery.where(SysUsers.type==filter_type)

            if search is not None:
                rquery = rquery.where(SysUsers.username.like("%{}%".format(search)))

            if not list_all:
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
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    } for m in db.session.execute(rquery)]
                }
            else:
                return [{
                    "id": m.id,
                    "username": m.username,
                    "type": m.type,
                    "active": m.active,
                    "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                    "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
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
    def post(self)->bool|dict:
        try:
            req = request.get_json()

            for usr in req:

                total = db.session.execute(
                    Select(func.count(SysUsers.id).label("total_lic")).where(SysUsers.type==usr["type"])
                ).first()
                if total is not None:
                    #A = Administrador, L = Lojista, I = Lojista (IA), R = Representante, V = Vendedor, C = Company User
                    if usr["type"]=="A" and total.total_lic == int(str(environ.get("F2B_MAX_ADM_LICENSE"))):
                        return {
                            "error_code": -1,
                            "error_details": "Número máximo de licenças Adm. atingido!",
                            "error_sql": ""
                        }
                    elif usr["type"]=="R" and total.total_lic == int(str(environ.get("F2B_MAX_REP_LICENSE"))):
                        return {
                            "error_code": -1,
                            "error_details": "Número máximo de licenças REP. atingido!",
                            "error_sql": ""
                        }
                    elif usr["type"]=="I" and total.total_lic == int(str(environ.get("F2B_MAX_SIA_LICENSE"))):
                        return {
                            "error_code": -1,
                            "error_details": "Número máximo de licenças I.A atingido!",
                            "error_sql": ""
                        }
                    elif usr["type"]=="L" and total.total_lic == int(str(environ.get("F2B_MAX_STR_LICENSE"))):
                        return {
                            "error_code": -1,
                            "error_details": "Número máximo de licenças Lojista atingido!",
                            "error_sql": ""
                        }
                    elif usr["type"]=="U" and total.total_lic == int(str(environ.get("F2B_MAX_USR_LICENSE"))):
                        return {
                            "error_code": -1,
                            "error_details": "Número máximo de licenças Colaborador atingido!",
                            "error_sql": ""
                        }

                    if usr["id"]==0:
                        user = SysUsers()
                        user.username = usr["username"]
                        user.password = user.hash_pwd(usr["password"])
                        user.type     = usr["type"]
                        db.session.add(user)
                        db.session.commit()

                        if usr["id_entity"]!="undefined":
                            usrEn = CmmUserEntity()
                            usrEn.id_user   = user.id
                            usrEn.id_entity = usr["id_entity"]
                            db.session.add(usrEn)
                            db.session.commit()
                    else:
                        user:SysUsers|None = SysUsers.query.get(usr["id"])
                        if user is not None:
                            user.username = usr["username"]
                            user.password = user.hash_pwd(usr["password"])
                            user.type     = usr["type"]
                            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_user.response(HTTPStatus.OK.value,"Exclui os dados de um usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def delete(self)->bool|dict:
        try:
            req = request.get_json()
            for id in req["ids"]:
                usr:SysUsers|None = SysUsers.query.get(id)
                if usr is not None:
                    usr.active = req["toTrash"]
                    db.session.commit()
            return True
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
            rquery = Select(SysUsers.username,
                                             SysUsers.type,
                                             SysUsers.active,
                                             CmmUserEntity.id_entity,
                                             SysUsers.date_created,
                                             SysUsers.date_updated)\
                                             .outerjoin(CmmUserEntity,CmmUserEntity.id_user==SysUsers.id)\
                                             .where(SysUsers.id==id)
            
            # _show_query(rquery)
            user = db.session.execute(rquery).first()

            return {
                "id": id,
                "username": None if user is None else user.username,
                "type": None if user is None else user.type,
                "active": False if user is None else user.active,
                "id_entity": None if user is None else user.id_entity,
                "password": None,
                "date_created": None if user is None else user.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                "date_updated": None if user is None else (user.date_updated.strftime("%Y-%m-%d %H:%M:%S") if user.date_updated is not None else None)
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_user.response(HTTPStatus.OK.value,"Salva dados de um usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            usr:SysUsers|None = SysUsers.query.get(id)
            if usr is not None:
                usr.username = req["username"]
                usr.password = usr.hash_pwd(req["password"])
                usr.type     = req["type"]
                db.session.commit()

                #caso trenha trocado de entidade para aquele usuario. Ex: era lojista e virou representante
                db.session.execute(Delete(CmmUserEntity).where(CmmUserEntity.id_user==id))
                db.session.commit()

                if req["id_entity"]!="undefined":
                        usrEn = CmmUserEntity()
                        setattr(usrEn,"id_user",id)
                        usrEn.id_entity = req["id_entity"]
                        db.session.add(usrEn)
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
    def delete(self,id:int):
        try:
            usr:SysUsers|None = SysUsers.query.get(id)
            if usr is not None:
                setattr(usr,"active",False)
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
        # req = request.get_json()
        query = Select(SysUsers)\
                     .outerjoin(CmmUserEntity,CmmUserEntity.id_user==SysUsers.id)\
                     .outerjoin(CmmLegalEntities,CmmLegalEntities.id==CmmUserEntity.id_entity)\
                     .outerjoin(CmmLegalEntityContact,CmmLegalEntityContact.id_legal_entity==CmmLegalEntities.id)\
                     .where(SysUsers.active.is_(True))\
                     .where(or_(
                         SysUsers.username==request.form.get("username"),
                         CmmLegalEntities.taxvat==request.form.get("username"),
                         and_(
                             CmmLegalEntityContact.contact_type==ContactType.EMAIL.value,
                             CmmLegalEntityContact.is_default.is_(True),
                             CmmLegalEntityContact.value==request.form.get("username")
                         )
                     ))
        usr = db.session.execute(query).first()[0] # type: ignore
        # usr = SysUsers.query.filter(and_(SysUsers.username==request.form.get("username"),SysUsers.active==True)).first()
        if usr is not None:

            #tenta buscar um profile
            idProfile = 0
            entity = CmmUserEntity.query.filter(CmmUserEntity.id_user==usr.id).first()
            if entity is not None:
                idProfile = entity.id_entity

            #verifica a senha criptografada anteriormente
            pwd = str(request.form.get("password")).encode()
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
        else:
            #tenta encontrar a entidade pelo usuario ou CNPJ/CPF
            entity = db.session.execute(Select(CmmLegalEntities.id).distinct()\
                .join(CmmLegalEntityContact,CmmLegalEntityContact.id_legal_entity==CmmLegalEntities.id)\
                .where(or_(
                CmmLegalEntities.taxvat==str(request.form.get("username")).replace(".","").replace("-","").replace("/",""),
                CmmLegalEntityContact.value==request.form.get("username")
                )
            )).first()
            if entity is not None:
                usr = SysUsers.query.filter(and_(SysUsers.id==(Select(CmmUserEntity.id_user).where(CmmUserEntity.id_entity==entity.id)),SysUsers.active==True)).first()
                if usr is not None:
                    #verifica a senha criptografada anteriormente
                    pwd = str(request.form.get("password")).encode()
                    if usr.check_pwd(pwd):
                        obj_retorno = {
                            "token_access": usr.get_token(),
                            "token_type": "Bearer",
                            "token_expire": usr.token_expire.strftime("%Y-%m-%d %H:%M:%S"),
                            "level_access": usr.type,
                            "id_user": usr.id,
                            "id_profile": entity.id
                        }
                        usr.is_authenticate = True
                        db.session.commit()
                        _save_log(entity.id,CustomerAction.SYSTEM_ACCESS,'Efetuou login')
                        return obj_retorno
        return -1 #usuario invalido
    
    @ns_user.response(HTTPStatus.OK.value,"Realiza a validacao do token do usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao verificar o token!")
    def put(self) -> bool:
        try:
            #print(request.get_json())
            req = request.get_json()
            retorno = SysUsers.check_token(req['token'])
            return False if retorno is None else retorno.token_expire.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return False
    
    @ns_user.response(HTTPStatus.OK.value,"Realiza a atualizacao do token do usuario")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao atualizar o token!")
    def get(self):
        try:
            usr:SysUsers|None = SysUsers.query.get(request.args.get("id"))
            if usr is not None:
                usr.renew_token()
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
            usr:SysUsers|None = SysUsers.query.get(id)
            if usr is not None:
                usr.logout()
                db.session.commit()
                entity = CmmUserEntity.query.filter(CmmUserEntity.id_user==id).first()
                if entity is not None:
                    _save_log(entity.id,CustomerAction.SYSTEM_ACCESS,'Efetuou logoff')
                return True
        except Exception:
            return False
        
ns_user.add_resource(UserAuthLogout,"/logout/<int:id>")


class UserUpdate(Resource):
    def __get_username(self,id,rule):
        reg = db.session.execute(Select(CmmLegalEntities.name).where(CmmLegalEntities.id==id)).first()
        if reg is not None:
            name = reg.name
            name = str(name).replace(".","")
            name = ''.join([i for i in name if not str(i).isdigit()])
            name = str(name.lower()\
                    .replace("ltda","")\
                    .replace("eireli","")\
                    .replace("'","")\
                    .replace("`","")\
                    .replace("´","")\
                    .replace("’","")\
                    .replace("”","")\
                    .replace("“","")).lstrip().rstrip()

            new_name = ""
            if rule=="FL":
                new_name = name.split(" ")[0]+"."+name.split(" ")[len(name.split(" "))-1]
            elif rule=="IL":
                new_name = name.split(" ")[0][0:1]+"."+name.split(" ")[len(name.split(" "))-1]
            else: #PI
                new_name = name.split(" ")[0]+"."+name.split(" ")[len(name.split(" "))-1][0:1]

            return new_name

    @ns_user.response(HTTPStatus.OK.value,"Cria um ou mais novo(s) usuário(s) no sistema")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar!")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            for id_entity in req["ids"]:

                exist_entity = db.session.execute(
                    Select(func.count().label("total")).select_from(CmmUserEntity)\
                        .where(CmmUserEntity.id_entity==id_entity)
                ).first()

                if exist_entity is None or exist_entity.total == 0:

                    exist_uname = db.session.execute(
                        Select(SysUsers.username,SysUsers.id)\
                        .where(SysUsers.username==self.__get_username(id_entity,req["rule"]))
                    ).first()

                    #forca o tipo do usuario a ser R quando for representante
                    entity_type = db.session.execute(Select(CmmLegalEntities.type).where(CmmLegalEntities.id==id_entity)).first()
                    if entity_type is not None:
                        if entity_type.type=='R' and req["type"]=='R':
                            new_type = 'R'
                        elif entity_type.type=='R' and req['type']!='R':
                            new_type = 'R'
                        elif entity_type.type=='C' and req['type']=="L":
                            new_type = req['type']
                        elif entity_type.type=='C' and req['type']=='I':
                            new_type = req['type']=="I"
                        else:
                            new_type = 'L' #forca como lojista basico se nao souber ou tiver indicado errado
                    else:
                        new_type = 'L'

                    if exist_uname is None:
                        usr = SysUsers()
                        setattr(usr,"username",(self.__get_username(id_entity,req["rule"])))
                        usr.password = usr.hash_pwd(req["password"])
                        setattr(usr,"type",new_type)
                        db.session.add(usr)
                        db.session.commit()

                        usrE = CmmUserEntity()
                        usrE.id_user   = usr.id
                        usrE.id_entity = id_entity
                        db.session.add(usrE)
                        db.session.commit()
                else:
                    #forca o tipo do usuario a ser R quando for representante
                    entity_type = db.session.execute(Select(CmmLegalEntities.type).where(CmmLegalEntities.id==id_entity)).first()
                    if entity_type=='R' and req["type"]=='R':
                        new_type = 'R'
                    elif entity_type=='R' and req['type']!='R':
                        new_type = 'R'
                    elif entity_type=='C' and req['type']=="L":
                        new_type = req['type']
                    elif entity_type=='C' and req['type']=='I':
                        new_type = req['type']=="I"
                    else:
                        new_type = 'L' #forca como lojista basico se nao souber ou tiver indicado errado

                    # atualiza apenas o username e o password
                    usrE = db.session.execute(Select(CmmUserEntity.id_user).where(CmmUserEntity.id_entity==id_entity)).first()
                    usr:SysUsers|None = SysUsers.query.get(0 if usrE is None else usrE.id_user)
                    if usr is not None:
                        usr.password = usr.hash_pwd(req["password"])
                        setattr(usr,"username",self.__get_username(id_entity,req["rule"]))
                        setattr(usr,"type",new_type)
                        db.session.commit()
                    
                #''.join([i for i in s if not i.isdigit()])
            # db.session.execute(Update(SysUsers),[{
            #     "id": m["id"],
            #     "active":m["active"],
            #     "type": m["type"]
            # }for m in req])
            # db.session.commit()
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
                Insert(SysUsers),[{
                    "username": usr["username"],
                    "password": SysUsers().hash_pwd(usr["password"]),
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

class UserPassword(Resource):
    @ns_user.response(HTTPStatus.OK.value,"Gera uma nova senha padrão para um usuário!")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao atualizar!")
    @auth.login_required
    def put(self):
        try:
            req = request.get_json()
            pwd = str(environ.get("F2B_TOKEN_KEY")).lower()+str(datetime.now().year)
            stmt = Select(SysUsers).where(SysUsers.id==req["id"])
            row = db.session.execute(stmt).first()
            usr: SysUsers | None = row[0] if row is not None else None
            if usr is not None:
                usr.password = usr.hash_pwd(pwd)
                db.session.commit()
                return pwd
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_user.response(HTTPStatus.OK.value,"Verifica se o e-mail existe no BD e envia mensagem para redefinição de senha!")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Falha ao atualizar!")
    def post(self):
        try:
            req = request.get_json()
            sended = False
            # so terah direito ao reset de senha se o usuario estiver ativo no sistema
            # o usuario eh desativado quando a entidade legal vai para a lixeira
            # porem o usuario tambem pode ser desativado diretamente no cadastro de 
            # usuarios
            exist = db.session.execute(
                Select(CmmLegalEntityContact.value,CmmLegalEntities.fantasy_name)\
                .join(CmmLegalEntities,CmmLegalEntities.id==CmmLegalEntityContact.id_legal_entity)\
                .join(CmmUserEntity,CmmUserEntity.id_entity==CmmLegalEntities.id)\
                .join(SysUsers,SysUsers.id==CmmUserEntity.id_user)\
                .where(and_(
                    SysUsers.active.is_(True),
                    CmmLegalEntityContact.value==req["email"]
                ))
            ).first()
            if exist is not None:
                sended = _send_email(
                    exist.value,
                    [],
                    "Fast2bee - Recuperação de Senha",
                    exist.fantasy_name,
                    MailTemplates.PWD_RECOVERY)
                return sended
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

ns_user.add_resource(UserPassword,"/password/")

class UserCount(Resource):
    @ns_user.response(HTTPStatus.OK.value,"Retorna o total de Usuarios por tipo")
    @ns_user.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_user.param("type","Tipo da Entidade","query",type=str,enum=['','A','L','R','C'])
    @auth.login_required
    def get(self):
        try:
            stmt = Select(func.count(SysUsers.id).label("total")).select_from(SysUsers)
            if(request.args.get("level")!=""):
                stmt = stmt.where(SysUsers.type==request.args.get("level"))
            row = db.session.execute(stmt).first()
            return 0 if row is None else row.total
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_user.hide
    def post(self):
        try:
            req = request.get_json()
            stmt = Select(func.count(SysUsers.id).label("total")).select_from(SysUsers)
            if(req["level"]!=""):
                stmt = stmt.where(SysUsers.type==req["level"])
            row = db.session.execute(stmt).first()
            return 0 if row is None else row.total
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
ns_user.add_resource(UserCount,'/count')