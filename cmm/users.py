from http import HTTPStatus
from typing import TypedDict
from flask_restx import Resource,fields,Namespace
from flask import request
from models import CmmUsers,db

api = Namespace("users",description="Operações para manipular dados de usuários do sistema")

#API Models
user_model = api.model(
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

class User(TypedDict):
    id:int
    username:str
    password:str
    name:str
    type:str

####################################################################################
#            INICIO DAS CLASSES QUE IRAO TRATAR OS GRUPOS DE USUARIOS.             #
####################################################################################
@api.route("/")
class UsersList(Resource):
    username:str
    password:str

    @api.response(HTTPStatus.OK.value,"Obtem a listagem de usuários",[user_model])
    @api.doc(description="Teste de documentacao")
    @api.param("page","Número da página de registros","query",type=int,required=True)
    @api.param("size","Número de registros por página","query",type=int,required=True,default=25)
    def get(self):

        rquery = CmmUsers.query.paginate(
            page=int(request.args.get("page")),
            per_page=int(request.args.get("per_page"))
        )

        #pedro maria
        return {
            "pagination":{
                "registers": rquery.total,
                "page": int(request.args.get("page")),
                "per_page": rquery.per_page,
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
            } for m in rquery.items ]
        }

    @api.response(HTTPStatus.OK.value,"Cria um novo usuário no sistema")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar novo usuário!")
    @api.param("name","Nome da pessoa","formData",required=True)
    @api.param("username","Login do usuário","formData",required=True)
    @api.param("password","Senha do usuário","formData",required=True)
    @api.param("type","Tipo do usuário","formData",required=True,type=chr)
    def post(self)->int:
        try:
            usr = CmmUsers()
            usr.name = request.form.get("name")
            usr.username = request.form.get("username")
            usr.password = request.form.get("password")
            usr.type     = request.form.get("type")
            db.session.add(usr)
            db.session.commit()
            return usr.id
        except:
            return 0


@api.route("/<int:id>")
@api.param("id","Id do registro")
class UserApi(Resource):

    @api.response(HTTPStatus.OK.value,"Obtem um registro de usuario",user_model)
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def get(self,id:int)->User:
        return CmmUsers.query.get(id).to_dict()

    @api.response(HTTPStatus.OK.value,"Salva dados de um usuario")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def post(self,id:int)->bool:
        try:
            usr = CmmUsers.query.get(id)
            usr.name = request.form.get("name")
            usr.username = request.form.get("username")
            usr.password = request.form.get("password")
            usr.type     = request.form.get("type")
            db.session.add(usr)
            db.session.commit()
            return True
        except:
            return False
    
    @api.response(HTTPStatus.OK.value,"Exclui os dados de um usuario")
    @api.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado")
    def delete(self,id:int)->bool:
        try:
            usr = CmmUsers.query.get(id)
            db.session.delete(usr)
            db.session.commit()
            return True
        except:
            return False